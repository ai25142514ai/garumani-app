import requests
import csv
import datetime
import re
from bs4 import BeautifulSoup

url = "https://www.dlsite.com/girls/ranking/day"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,ja-JP;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
cookies = {
    "adultchecked": "1",
    "locale": "ja_JP",
}

try:
    session = requests.Session()
    session.get("https://www.dlsite.com/girls/", headers=headers, cookies=cookies, timeout=15)
    res = session.get(url, headers=headers, cookies=cookies, timeout=20)
    res.encoding = res.apparent_encoding
    html = res.text

    soup = BeautifulSoup(html, "lxml")

    # .work_nameが30件あることがわかったので、その親要素を使う
    work_names = soup.select(".work_name")
    print(f".work_name件数: {len(work_names)}")

    now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M")
    rows = []

    for i, work_name_el in enumerate(work_names[:30], 1):
        try:
            # 親要素をさかのぼって作品カード全体を取得
            item = work_name_el.find_parent("li") or work_name_el.find_parent("div")

            title_el = work_name_el.select_one("a") or work_name_el
            title = title_el.get_text(strip=True)

            circle_el = None
            if item:
                circle_el = (
                    item.select_one(".maker_name a") or
                    item.select_one(".circle_name a") or
                    item.select_one(".maker_name") or
                    item.select_one(".brand_name")
                )
            circle = circle_el.get_text(strip=True) if circle_el else "不明"

            raw = item.get_text().replace(",", "") if item else ""
            dl_match = re.search(r"(\d+)DL", raw)
            dl = dl_match.group(1) if dl_match else "0"

            price_el = None
            if item:
                price_el = (
                    item.select_one(".work_price") or
                    item.select_one(".price")
                )
            price_raw = re.sub(r"\D", "", price_el.get_text()) if price_el else "0"
            price = price_raw if price_raw else "0"

            img_el = item.select_one("img") if item else None
            img = ""
            if img_el:
                img = img_el.get("data-src") or img_el.get("src") or ""
                if img.startswith("//"):
                    img = "https:" + img

            genres_els = item.select(".work_category a") or item.select(".tag a") if item else []
            genres = "|".join([g.get_text(strip=True) for g in genres_els])

            rows.append([i, title, circle, dl, price, genres, img, now])
            print(f"  {i}. {title[:30]}")

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
