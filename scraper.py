import requests
from bs4 import BeautifulSoup
import csv
import datetime
import re

url = "https://www.dlsite.com/girls/ranking/day"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja-JP,ja;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

try:
    res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=20)
    print(f"ステータス: {res.status_code}")
    soup = BeautifulSoup(res.content, "lxml")

    items = soup.select(".n_worklist_item") or soup.select(".work_1column") or soup.select("li.search_result_img_box_inner")
    print(f"取得件数: {len(items)}")

    now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M")
    rows = []

    for i, item in enumerate(items[:30], 1):
        try:
            title_el = item.select_one(".work_name a") or item.select_one("dt a")
            title = title_el.get_text(strip=True) if title_el else "不明"

            circle_el = item.select_one(".maker_name a") or item.select_one(".circle_name a")
            circle = circle_el.get_text(strip=True) if circle_el else "不明"

            raw = item.get_text().replace(",", "")
            dl_match = re.search(r"(\d+)DL", raw)
            dl = dl_match.group(1) if dl_match else "0"

            price_el = item.select_one(".work_price") or item.select_one(".price")
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
        except Exception as e:
            print(f"行{i}エラー: {e}")
            continue

    with open("ranking.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "title", "circle", "dl", "price", "genres", "img", "date"])
        writer.writerows(rows)

    print(f"CSV保存完了: {len(rows)}件")

except Exception as e:
    print(f"全体エラー: {e}")
