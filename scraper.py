import requests
import json
import datetime
import re
import time
import os
from bs4 import BeautifulSoup

RANKING_URL = "https://www.dlsite.com/girls-touch/ranking/day"

HISTORY_FILE = "ranking_history.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,ja-JP;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
COOKIES = {
    "adultchecked": "1",
    "locale": "ja_JP",
}

def get_session():
    session = requests.Session()
    session.get("https://www.dlsite.com/girls/", headers=HEADERS, cookies=COOKIES, timeout=15)
    return session

def get_ranking_list(session):
    res = session.get(RANKING_URL, headers=HEADERS, cookies=COOKIES, timeout=20)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "lxml")

    items = []
    work_names = soup.select(".work_name")
    print(f"ランキング一覧取得: {len(work_names)}件")

    for i, el in enumerate(work_names[:30], 1):
        a = el.select_one("a")
        if not a:
            continue
        title = a.get_text(strip=True)
        href = a.get("href", "")
        if href.startswith("//"):
            href = "https:" + href
        elif href.startswith("/"):
            href = "https://www.dlsite.com" + href
        items.append({"rank": i, "title": title, "url": href})

    return items

def get_work_detail(session, url):
    try:
        res = session.get(url, headers=HEADERS, cookies=COOKIES, timeout=20)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "lxml")

        img = ""
        img_el = soup.select_one("#work_img_main img") or soup.select_one(".slider_img img") or soup.select_one("meta[property='og:image']")
        if img_el:
            if img_el.name == "meta":
                img = img_el.get("content", "")
            else:
                img = img_el.get("src") or img_el.get("data-src") or ""
            if img.startswith("//"):
                img = "https:" + img

        circle = ""
        author = ""
        release_date = ""
        dl_count = "0"
        price = "0"
        tags = []

        table = soup.select_one("#work_outline")
        if table:
            rows = table.select("tr")
            for row in rows:
                th = row.select_one("th")
                td = row.select_one("td")
                if not th or not td:
                    continue
                label = th.get_text(strip=True)

                if "サークル" in label or "ブランド" in label:
                    circle = td.get_text(strip=True)
                elif "作家" in label or "著者" in label or "作者" in label:
                    author = td.get_text(strip=True)
                elif "発売日" in label or "販売日" in label:
                    release_date = td.get_text(strip=True)
                elif "ジャンル" in label:
                    tags = [a.get_text(strip=True) for a in td.select("a")]
                elif "DL数" in label or "ダウンロード数" in label:
                    raw = td.get_text().replace(",", "")
                    m = re.search(r"(\d+)", raw)
                    dl_count = m.group(1) if m else "0"

        price_el = soup.select_one(".price_container .price") or soup.select_one(".work_buy_content .price")
        if price_el:
            raw = re.sub(r"\D", "", price_el.get_text())
            price = raw if raw else "0"

        if dl_count == "0":
            dl_el = soup.select_one(".dl_count") or soup.select_one("[class*='dl_count']")
            if dl_el:
                raw = dl_el.get_text().replace(",", "")
                m = re.search(r"(\d+)", raw)
                dl_count = m.group(1) if m else "0"

        return {
            "circle": circle,
            "author": author,
            "release_date": release_date,
            "dl_count": int(dl_count) if dl_count.isdigit() else 0,
            "price": int(price) if price.isdigit() else 0,
            "tags": tags,
            "img": img,
        }

    except Exception as e:
        print(f"  詳細取得エラー: {e}")
        return {
            "circle": "", "author": "", "release_date": "",
            "dl_count": 0, "price": 0, "tags": [], "img": ""
        }

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def main():
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    date_key = datetime.datetime.now().strftime("%Y-%m-%d")

    print(f"=== スクレイピング開始: {now} ===")

    session = get_session()

    ranking_items = get_ranking_list(session)
    if not ranking_items:
        print("ランキング取得失敗")
        return

    results = []
    for item in ranking_items:
        print(f"  [{item['rank']:02d}] {item['title'][:25]}...")
        detail = get_work_detail(session, item["url"])
        results.append({
            "rank": item["rank"],
            "title": item["title"],
            "url": item["url"],
            **detail
        })
        time.sleep(0.8)

    with open("ranking_data.json", "w", encoding="utf-8") as f:
        json.dump({
            "date": now,
            "date_key": date_key,
            "items": results
        }, f, ensure_ascii=False, indent=2)

    history = load_history()
    history = [h for h in history if h.get("date_key") != date_key]
    history.append({
        "date": now,
        "date_key": date_key,
        "items": results
    })
    history = sorted(history, key=lambda x: x["date_key"])[-90:]
    save_history(history)

    tag_counts = {}
    for item in results:
        for tag in item.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
    top_tags = sorted(tag_counts.items(), key=lambda x: -x[1])[:20]

    tag_summary = {
        "date": now,
        "date_key": date_key,
        "tags": [{"tag": t, "count": c} for t, c in top_tags]
    }
    with open("tag_ranking.json", "w", encoding="utf-8") as f:
        json.dump(tag_summary, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完了: {len(results)}件保存 ===")
    print(f"上位タグ: {', '.join([t for t, _ in top_tags[:5]])}")

if __name__ == "__main__":
    main()
