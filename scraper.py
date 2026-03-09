import requests
import json
import os
import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
date_str = now.strftime(”%Y-%m-%d %H:%M”)
date_key = now.strftime(”%Y-%m-%d”)

RANKING_URL = “https://www.dlsite.com/girls-touch/ranking/day”
RANKING_FILE = “ranking_data.json”
HISTORY_FILE = “ranking_history.json”
TAG_FILE = “tag_ranking.json”
MAX_HISTORY = 90

UA = “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36”
HEADERS = {“User-Agent”: UA, “Accept-Language”: “ja,en;q=0.9”}

def get_ranking():
res = requests.get(RANKING_URL, headers=HEADERS, timeout=30)
res.encoding = “utf-8”
soup = BeautifulSoup(res.text, “lxml”)
items = []
for row in soup.select(“tr.ranking_list_item”):
try:
re = row.select_one(“td.ranking_num”)
te = row.select_one(“dt.work_name a”)
if not re or not te:
continue
rank = int(re.text.strip())
title = te.text.strip()
url = te.get(“href”, “”)
if url.startswith(”//”):
url = “https:” + url
ie = row.select_one(“img”)
img = “”
if ie:
img = ie.get(“src”) or ie.get(“data-src”) or “”
if img.startswith(”//”):
img = “https:” + img
items.append({
“rank”: rank, “title”: title, “url”: url, “img”: img,
“circle”: “”, “author”: “”, “release_date”: “”,
“dl_count”: 0, “price”: 0, “tags”: []
})
except Exception as e:
print(“row error:”, e)
return items

def get_detail(url):
try:
time.sleep(0.8)
res = requests.get(url, headers=HEADERS, timeout=20)
res.encoding = “utf-8”
soup = BeautifulSoup(res.text, “lxml”)
circle = author = release_date = “”
dl_count = price = 0
tags = []
c = soup.select_one(“span.maker_name a”) or soup.select_one(“a.maker_name”)
if c:
circle = c.text.strip()
for tr in soup.select(“table#work_outline tr”):
th = tr.select_one(“th”)
td = tr.select_one(“td”)
if not th or not td:
continue
lb = th.text.strip()
if “\u4f5c\u8005” in lb or “\u8457\u8005” in lb:
author = td.text.strip()
elif “\u8ca9\u58f2\u65e5” in lb:
release_date = td.text.strip()
elif “\u30c0\u30a6\u30f3\u30ed\u30fc\u30c9” in lb or “DL” in lb:
try:
dl_count = int(td.text.strip().replace(”,”, “”).replace(”\u4ef6”, “”))
except Exception:
pass
pe = soup.select_one(“span.price”) or soup.select_one(”.work_price”)
if pe:
try:
price = int(pe.text.strip().replace(”,”, “”).replace(”\u5186”, “”).replace(”\xa5”, “”))
except Exception:
pass
for a in soup.select(“div.main_genre a, a.genre_tag, div.work_genre a”):
t = a.text.strip()
if t:
tags.append(t)
return {
“circle”: circle, “author”: author, “release_date”: release_date,
“dl_count”: dl_count, “price”: price, “tags”: tags
}
except Exception as e:
print(“detail error:”, e)
return {}

def build_tag_data(items):
tc = {}
for item in items:
for tag in item.get(“tags”, []):
tc[tag] = tc.get(tag, 0) + 1
st = sorted(tc.items(), key=lambda x: x[1], reverse=True)
return {“tags”: [{“tag”: t, “count”: c} for t, c in st[:30]]}

def load_history():
if os.path.exists(HISTORY_FILE):
with open(HISTORY_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return []

def save_history(history, entry):
history = [d for d in history if d.get(“date_key”) != date_key]
history.append(entry)
history = sorted(history, key=lambda x: x[“date_key”])[-MAX_HISTORY:]
with open(HISTORY_FILE, “w”, encoding=“utf-8”) as f:
json.dump(history, f, ensure_ascii=False, indent=2)
return history

print(“scraping…”)
items = get_ranking()
print(len(items), “items found”)

for item in items:
print(item[“rank”], item[“title”][:20])
item.update(get_detail(item[“url”]))

rd = {“date”: date_str, “date_key”: date_key, “items”: items}
td = build_tag_data(items)

with open(RANKING_FILE, “w”, encoding=“utf-8”) as f:
json.dump(rd, f, ensure_ascii=False, indent=2)
with open(TAG_FILE, “w”, encoding=“utf-8”) as f:
json.dump(td, f, ensure_ascii=False, indent=2)

history = load_history()
history = save_history(history, rd)

print(“done”)
