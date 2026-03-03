import requests
import csv
import datetime
import re

url = "https://www.dlsite.com/girls/ranking/day"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,ja-JP;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}
cookies = {
    "adultchecked": "1",
    "locale": "ja_JP",
}

try:
    session = requests.Session()
    session.get("https://www.dlsite.com/girls/", headers=headers, cookies=cookies, timeout=15)
    res = session.get(url, headers=headers, cookies=cookies, timeout=20)
    print(f"ステータス: {res.status_code}")
    print(f"サイズ: {len(res.content)} bytes")

    from bs4 import BeautifulSoup
    soup = BeautifulSoup(res.content, "lxml")

    # 複数のセレクタを試す
    items = (
        soup.select("li.search_result_img_box_inner") or
        soup.select(".n_worklist_item") or
        soup.select(".work_1column") or
        soup.select("ul.work_1column_list > li") or
        soup.select(".ranking_list li")
    )
    print(f"取得件数: {len(items)}")

    if not items:
        # HTMLの構造確認用
        print("HTMLサンプル:")
        print(soup.prettify()[:2000])

    now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M")
    rows = []

    for i, item in enumerate(items[:30], 1):
        try:
            title_el = (
                item.select_one(".work_name a") or
                item.select_one("dt a") or
                item.select_one("a.work_name") or
                item.select_one("h2 a")
            )
            title = title_el.get_text(strip=True) if title_el else "不明"

            circle_el = (
                item.select_one(".maker_name a") or
                item.select_one(".circle_name a") or
                item.select_one(".maker_name") or
                item.select_one(".brand_name a")
            )
            circle = circle_el.get_text(strip=True) if circle_el else "不明"

            raw = item.get_text().replace(",", "")
            dl_match = re.search(r"(\d+)DL", raw)
            dl = dl_match.group(1) if dl_match else "0"

            price_el = (
                item.select_one(".work_price") or
                item.select_one(".price") or
                item.select_one(".work_price_wrap")
            )
            price_raw = re.sub(r"\D", "", price_el.get_text()) if price_el else "0"
            price = price_raw if price_raw else "0"

            img_el = item.select_one("img")
            img = ""
            if img_el:
                img = img_el.get("data-src") or img_el.get("src") or ""
                if img.startswith("//"):
                    img = "https:" + img

            genres_els = item.select(".work_category a") or item.select(".tag a")
            genres = "|".join([g.get_text(strip=True) for g in genres_els])

            rows.append([i, title, circle, dl, price, genres, img, now])
            print(f"  {i}. {title[:20]}")
        except Exception as e:
            print(f"行{i}エラー: {e}")
            continue

    with open("ranking.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "title", "circle", "dl", "price", "genres", "img", "date"])
        writer.writerows(rows)

    print(f"完了: {len(rows)}件保存")

except Exception as e:
    print(f"全体エラー: {e}")
    import traceback
    traceback.print_exc()
