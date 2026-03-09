import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime, timezone, timedelta

RANKING_URL = "https://www.dlsite.com/girls-touch/ranking/day"
HISTORY_FILE = “ranking_history.json”
RANKING_FILE = “ranking_data.json”
TAG_FILE = “tag_ranking.json”
INDEX_FILE = “index.html”
MAX_HISTORY_DAYS = 90

JST = timezone(timedelta(hours=9))
now = datetime.now(JST)
date_str = now.strftime(”%Y-%m-%d %H:%M”)
date_key = now.strftime(”%Y-%m-%d”)

HEADERS = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36”,
“Accept-Language”: “ja,en;q=0.9”,
}

def scrape_ranking():
res = requests.get(RANKING_URL, headers=HEADERS, timeout=30)
res.encoding = “utf-8”
soup = BeautifulSoup(res.text, “lxml”)
rows = soup.select(“tr.ranking_list_item”)
items = []
for row in rows:
try:
rank_el = row.select_one(“td.ranking_num”)
title_el = row.select_one(“dt.work_name a”)
if not rank_el or not title_el:
continue
rank = int(rank_el.text.strip())
title = title_el.text.strip()
url = title_el.get(“href”, “”)
if url and url.startswith(”//”):
url = “https:” + url
img_el = row.select_one(“img”)
img = “”
if img_el:
img = img_el.get(“src”) or img_el.get(“data-src”) or “”
if img.startswith(”//”):
img = “https:” + img
items.append({“rank”: rank, “title”: title, “url”: url, “img”: img,
“circle”: “”, “author”: “”, “release_date”: “”, “dl_count”: 0, “price”: 0, “tags”: []})
except Exception as e:
print(f”Row error: {e}”)
continue
return items

def scrape_detail(url):
try:
time.sleep(0.8)
res = requests.get(url, headers=HEADERS, timeout=20)
res.encoding = “utf-8”
soup = BeautifulSoup(res.text, “lxml”)
circle = “”
author = “”
release_date = “”
dl_count = 0
price = 0
tags = []
circle_el = soup.select_one(“span.maker_name a”) or soup.select_one(“a.maker_name”)
if circle_el:
circle = circle_el.text.strip()
for tr in soup.select(“table#work_outline tr”):
th = tr.select_one(“th”)
td = tr.select_one(“td”)
if not th or not td:
continue
label = th.text.strip()
if “作者” in label or “著者” in label:
author = td.text.strip()
elif “販売日” in label or “更新日” in label:
release_date = td.text.strip()
elif “ダウンロード” in label or “DL数” in label or “販売数” in label:
try:
dl_count = int(td.text.strip().replace(”,”, “”).replace(“件”, “”))
except:
pass
price_el = soup.select_one(“span.price”) or soup.select_one(”.work_price”)
if price_el:
try:
price = int(price_el.text.strip().replace(”,”, “”).replace(“円”, “”).replace(“¥”, “”).replace(”\xa5”, “”))
except:
pass
for a in soup.select(“div.main_genre a, a.genre_tag, div.work_genre a”):
t = a.text.strip()
if t:
tags.append(t)
return {“circle”: circle, “author”: author, “release_date”: release_date,
“dl_count”: dl_count, “price”: price, “tags”: tags}
except Exception as e:
print(f”Detail error {url}: {e}”)
return {}

def build_tag_ranking(items):
tag_count = {}
for item in items:
for tag in item.get(“tags”, []):
tag_count[tag] = tag_count.get(tag, 0) + 1
sorted_tags = sorted(tag_count.items(), key=lambda x: x[1], reverse=True)
return {“tags”: [{“tag”: t, “count”: c} for t, c in sorted_tags[:30]]}

def load_history():
if os.path.exists(HISTORY_FILE):
with open(HISTORY_FILE, “r”, encoding=“utf-8”) as f:
return json.load(f)
return []

def save_history(history, new_entry):
history = [d for d in history if d.get(“date_key”) != date_key]
history.append(new_entry)
history = sorted(history, key=lambda x: x[“date_key”])[-MAX_HISTORY_DAYS:]
with open(HISTORY_FILE, “w”, encoding=“utf-8”) as f:
json.dump(history, f, ensure_ascii=False, indent=2)
return history

def build_index_html(ranking_data, tag_data, history_data):
r_json = json.dumps(ranking_data, ensure_ascii=False)
t_json = json.dumps(tag_data, ensure_ascii=False)
h_json = json.dumps(history_data, ensure_ascii=False)
return f’’’<!DOCTYPE html>

<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>がるまにランキング</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&family=Kaisei+Decol:wght@700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{{--pink:#ff4da6;--pink-light:#ff80c8;--purple:#b44dff;--bg:#0d0010;--bg2:#130018;--card-bg:#1a0025;--card-border:#3a1050;--text:#f0e0ff;--text-muted:#a080b0;}}
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{background:var(--bg);color:var(--text);font-family:'Noto Sans JP',sans-serif;min-height:100vh;overflow-x:hidden;}}
body::before{{content:'';position:fixed;inset:0;background:linear-gradient(rgba(180,77,255,0.04) 1px,transparent 1px),linear-gradient(90deg,rgba(180,77,255,0.04) 1px,transparent 1px);background-size:40px 40px;pointer-events:none;z-index:0;}}
header{{position:sticky;top:0;z-index:100;background:rgba(13,0,16,0.92);backdrop-filter:blur(12px);border-bottom:1px solid rgba(180,77,255,0.3);padding:12px 16px;}}
.header-inner{{display:flex;align-items:center;justify-content:space-between;max-width:600px;margin:0 auto;}}
.logo{{font-family:'Kaisei Decol',serif;font-size:20px;background:linear-gradient(135deg,var(--pink),var(--purple));-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 8px rgba(255,77,166,0.5));}}
.last-updated{{font-size:10px;color:var(--text-muted);}}
.tabs{{display:flex;gap:8px;padding:14px 16px 0;max-width:600px;margin:0 auto;overflow-x:auto;scrollbar-width:none;}}
.tabs::-webkit-scrollbar{{display:none;}}
.tab{{flex-shrink:0;padding:7px 16px;border-radius:20px;font-size:13px;font-weight:700;cursor:pointer;border:1px solid var(--card-border);background:var(--card-bg);color:var(--text-muted);transition:all 0.2s;}}
.tab.active{{background:linear-gradient(135deg,var(--pink),var(--purple));border-color:transparent;color:white;}}
main{{max-width:600px;margin:0 auto;padding:14px 12px 80px;position:relative;z-index:1;}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(12px);}}to{{opacity:1;transform:translateY(0);}}}}
@keyframes neonPulse{{0%,100%{{box-shadow:0 0 8px rgba(255,215,0,0.3);}}50%{{box-shadow:0 0 20px rgba(255,215,0,0.5),0 0 40px rgba(255,215,0,0.2);}}}}
.rank-card{{background:var(--card-bg);border:1px solid var(--card-border);border-radius:14px;margin-bottom:10px;overflow:hidden;display:flex;transition:transform 0.15s;animation:fadeUp 0.3s ease both;cursor:pointer;text-decoration:none;color:inherit;}}
.rank-card:active{{transform:scale(0.98);}}
.rank-card.mega-hit{{border-color:rgba(255,215,0,0.6);animation:fadeUp 0.3s ease both,neonPulse 2.5s ease-in-out infinite;}}
.thumb-wrap{{width:90px;min-width:90px;height:120px;overflow:hidden;position:relative;background:var(--bg2);}}
.thumb-wrap img{{width:100%;height:100%;object-fit:cover;display:block;}}
.thumb-placeholder{{width:100%;height:100%;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1a0025,#2a0040);font-size:28px;}}
.rank-badge{{position:absolute;top:6px;left:6px;width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:900;z-index:2;}}
.rank-badge.r1{{background:linear-gradient(135deg,#ffd700,#ffaa00);color:#000;}}
.rank-badge.r2{{background:linear-gradient(135deg,#c0c0c0,#888);color:#000;}}
.rank-badge.r3{{background:linear-gradient(135deg,#cd7f32,#8b4513);color:#fff;}}
.rank-badge.other{{background:rgba(0,0,0,0.7);color:var(--text-muted);border:1px solid var(--card-border);}}
.card-info{{flex:1;padding:10px 12px;display:flex;flex-direction:column;gap:5px;min-width:0;}}
.card-title{{font-size:13px;font-weight:700;line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;}}
.card-circle{{font-size:11px;color:var(--pink-light);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.card-meta{{display:flex;gap:10px;flex-wrap:wrap;}}
.meta-item{{font-size:11px;color:var(--text-muted);}}
.meta-item.dl{{color:var(--pink-light);font-weight:700;}}
.meta-item.price{{color:#aaffcc;}}
.card-tags{{display:flex;gap:4px;flex-wrap:wrap;margin-top:2px;}}
.tag{{font-size:10px;padding:2px 7px;border-radius:10px;background:rgba(180,77,255,0.15);border:1px solid rgba(180,77,255,0.25);color:#d0a0ff;white-space:nowrap;}}
.section-title{{font-family:'Kaisei Decol',serif;font-size:16px;color:var(--pink);margin:16px 0 10px;display:flex;align-items:center;gap:8px;}}
.section-title::after{{content:'';flex:1;height:1px;background:linear-gradient(90deg,rgba(255,77,166,0.4),transparent);}}
.tag-rank-list{{display:flex;flex-direction:column;gap:8px;}}
.tag-rank-item{{display:flex;align-items:center;gap:10px;background:var(--card-bg);border:1px solid var(--card-border);border-radius:10px;padding:10px 14px;animation:fadeUp 0.3s ease both;}}
.tag-rank-num{{font-size:18px;font-weight:900;min-width:28px;color:var(--purple);}}
.tag-rank-num.t1{{color:#ffd700;}}
.tag-rank-num.t2{{color:#c0c0c0;}}
.tag-rank-num.t3{{color:#cd7f32;}}
.tag-rank-name{{flex:1;font-size:14px;font-weight:700;}}
.tag-rank-bar-wrap{{width:80px;}}
.tag-rank-bar{{height:6px;border-radius:3px;background:linear-gradient(90deg,var(--pink),var(--purple));}}
.tag-rank-count{{font-size:11px;color:var(--text-muted);margin-top:3px;text-align:right;}}
.chart-card{{background:var(--card-bg);border:1px solid var(--card-border);border-radius:14px;padding:16px;margin-bottom:14px;}}
.chart-card canvas{{max-height:220px;}}
.chart-note{{font-size:10px;color:var(--text-muted);text-align:center;margin-top:8px;}}
.error-msg{{text-align:center;padding:40px 20px;color:var(--text-muted);}}
footer{{position:fixed;bottom:0;left:0;right:0;background:rgba(13,0,16,0.95);border-top:1px solid rgba(180,77,255,0.2);padding:8px 16px;text-align:center;font-size:10px;color:var(--text-muted);z-index:100;}}
.heart-particle{{position:fixed;pointer-events:none;z-index:9999;animation:heartFloat 1.2s ease-out forwards;user-select:none;}}
@keyframes heartFloat{{0%{{opacity:1;transform:translateY(0) scale(1);}}100%{{opacity:0;transform:translateY(-120px) scale(1.6);}}}}
</style>
</head>
<body>
<header>
  <div class="header-inner">
    <div class="logo">&#x1F49C; がるまにランキング</div>
    <div class="last-updated" id="lastUpdated"></div>
  </div>
</header>
<div class="tabs">
  <div class="tab active" onclick="switchTab('ranking')">&#x1F3C6; ランキング</div>
  <div class="tab" onclick="switchTab('tags')">&#x1F3F7;&#xFE0F; タグ人気</div>
  <div class="tab" onclick="switchTab('graph')">&#x1F4C8; 推移グラフ</div>
</div>
<main>
  <div id="rankingSection"></div>
  <div id="tagsSection" style="display:none"></div>
  <div id="graphSection" style="display:none"></div>
</main>
<footer>データは毎日深夜0時頃に自動更新されます</footer>
<script>
var RANKING_DATA = {r_json};
var TAG_DATA = {t_json};
var HISTORY_DATA = {h_json};
var chartInstances = {{}};

function esc(s) {{
var d = document.createElement(‘div’);
d.textContent = String(s || ‘’);
return d.innerHTML;
}}

function switchTab(tab) {{
var names = [‘ranking’,‘tags’,‘graph’];
document.querySelectorAll(’.tab’).forEach(function(el,i){{ el.classList.toggle(‘active’, names[i]===tab); }});
names.forEach(function(n){{ document.getElementById(n+‘Section’).style.display = n===tab?‘block’:‘none’; }});
}}

function spawnHearts(x,y) {{
var hearts = [’\u{1F49C}’,’\u{1F497}’,’\u{1F495}’,’\u2728’,’\u{1F4AB}’];
for(var i=0;i<5;i++){{
(function(idx){{
setTimeout(function(){{
var el = document.createElement(‘div’);
el.className = ‘heart-particle’;
el.textContent = hearts[Math.floor(Math.random()*hearts.length)];
el.style.left = (x+(Math.random()-0.5)*60)+‘px’;
el.style.top = (y+(Math.random()-0.5)*20)+‘px’;
el.style.fontSize = (14+Math.random()*14)+‘px’;
document.body.appendChild(el);
setTimeout(function(){{ el.remove(); }}, 1300);
}}, idx*80);
}})(i);
}}
}}
document.addEventListener(‘click’, function(e){{ if(e.target.closest(’.rank-card’)) spawnHearts(e.clientX, e.clientY); }});

function renderRanking(data) {{
document.getElementById(‘lastUpdated’).textContent = data.date ? data.date+’ 更新’ : ‘’;
var items = data.items || [];
var html = ‘’;
items.forEach(function(item,idx){{
var isMega = (item.dl_count||0) >= 10000;
var tags = (item.tags||[]).slice(0,4);
var dlStr = item.dl_count ? item.dl_count.toLocaleString()+‘DL’ : ‘’;
var priceStr = item.price ? item.price.toLocaleString()+‘円’ : ‘’;
var circle = item.circle || item.author || ‘’;
var badge = item.rank<=3 ? ‘r’+item.rank : ‘other’;
var imgHtml = item.img ? ‘<img src="'+item.img+'" alt="" loading="lazy" onerror="this.style.display=\'none\'">’ : ‘<div class="thumb-placeholder">📖</div>’;
html += ‘<a class="rank-card'+(isMega?' mega-hit':'')+'" href="'+(item.url||'#')+'" target="_blank" rel="noopener" style="animation-delay:'+idx*0.04+'s">’;
html += ‘<div class="thumb-wrap">’+imgHtml+’<div class="rank-badge '+badge+'">’+item.rank+’</div></div>’;
html += ‘<div class="card-info"><div class="card-title">’+esc(item.title)+’</div>’;
if(circle) html += ‘<div class="card-circle">’+esc(circle)+’</div>’;
html += ‘<div class="card-meta">’;
if(dlStr) html += ‘<span class="meta-item dl">’+esc(dlStr)+(isMega?’ <span style="font-size:9px;background:linear-gradient(135deg,#ffd700,#ffaa00);color:#000;padding:1px 5px;border-radius:4px;font-weight:900;">1万超え</span>’:’’)+’</span>’;
if(priceStr) html += ‘<span class="meta-item price">’+priceStr+’</span>’;
if(item.release_date) html += ‘<span class="meta-item">’+esc(item.release_date)+’</span>’;
html += ‘</div>’;
if(tags.length){{ html += ‘<div class="card-tags">’; tags.forEach(function(t){{ html += ‘<span class="tag">’+esc(t)+’</span>’; }}); html += ‘</div>’; }}
html += ‘</div></a>’;
}});
document.getElementById(‘rankingSection’).innerHTML = html;
}}

function renderTags(data) {{
var tags = data.tags || [];
var max = tags.length ? tags[0].count : 1;
var html = ‘<div class="section-title">🏷️ 今日の人気タグ</div><div class="tag-rank-list">’;
tags.forEach(function(t,i){{
var cls = i<3 ? ‘t’+(i+1) : ‘’;
html += ‘<div class="tag-rank-item" style="animation-delay:'+i*0.05+'s">’;
html += ‘<div class="tag-rank-num '+cls+'">’+(i+1)+’</div>’;
html += ‘<div class="tag-rank-name">’+esc(t.tag)+’</div>’;
html += ‘<div class="tag-rank-bar-wrap"><div class="tag-rank-bar" style="width:'+Math.round(t.count/max*100)+'%"></div>’;
html += ‘<div class="tag-rank-count">’+t.count+‘作品</div></div></div>’;
}});
html += ‘</div>’;
document.getElementById(‘tagsSection’).innerHTML = html;
}}

function renderGraph(history) {{
if(!history||history.length===0){{
document.getElementById(‘graphSection’).innerHTML=’<div class="error-msg">履歴データがまだありません。<br>毎日蓄積されていきます</div>’; return;
}}
var tagByDate={{}};
history.forEach(function(day){{
tagByDate[day.date_key]={{}};
(day.items||[]).forEach(function(item){{
(item.tags||[]).forEach(function(tag){{ tagByDate[day.date_key][tag]=(tagByDate[day.date_key][tag]||0)+1; }});
}});
}});
var dates=Object.keys(tagByDate).sort();
var totalTagCount={{}};
dates.forEach(function(d){{ Object.entries(tagByDate[d]).forEach(function(e){{ totalTagCount[e[0]]=(totalTagCount[e[0]]||0)+e[1]; }}); }});
var topTags=Object.entries(totalTagCount).sort(function(a,b){{return b[1]-a[1];}}).slice(0,8).map(function(e){{return e[0];}});
var colors=[’#ff4da6’,’#b44dff’,’#ff80c8’,’#7a1fa2’,’#ff9de2’,’#d084ff’,’#ffaad4’,’#9b59b6’];
var datasets=topTags.map(function(tag,i){{
return {{label:tag,data:dates.map(function(d){{return tagByDate[d][tag]||0;}}),borderColor:colors[i%colors.length],backgroundColor:colors[i%colors.length]+‘22’,borderWidth:2,pointRadius:3,tension:0.4,fill:false}};
}});
if(chartInstances.tagTrend) chartInstances.tagTrend.destroy();
document.getElementById(‘graphSection’).innerHTML=
‘<div class="section-title">📈 タグ人気の推移</div>’+
‘<div class="chart-card"><canvas id="chartTagTrend"></canvas>’+
‘<div class="chart-note">過去’+dates.length+‘日間のランキング上位タグの出現数推移</div></div>’;
chartInstances.tagTrend=new Chart(document.getElementById(‘chartTagTrend’).getContext(‘2d’),{{
type:‘line’,data:{{labels:dates.map(function(d){{return d.slice(5);}}),datasets:datasets}},
options:{{responsive:true,plugins:{{legend:{{position:‘bottom’,labels:{{color:’#d0a0ff’,font:{{size:10}},boxWidth:12,padding:8}}}},tooltip:{{backgroundColor:’#1a0025’,borderColor:’#3a1050’,borderWidth:1,titleColor:’#ff4da6’,bodyColor:’#f0e0ff’}}}},scales:{{x:{{ticks:{{color:’#a080b0’,font:{{size:10}}}},grid:{{color:‘rgba(180,77,255,0.08)’}}}},y:{{ticks:{{color:’#a080b0’,font:{{size:10}}}},grid:{{color:‘rgba(180,77,255,0.08)’}},beginAtZero:true}}}}}}
}});
}}

renderRanking(RANKING_DATA);
renderTags(TAG_DATA);
renderGraph(HISTORY_DATA);
</script>

</body>
</html>'''

# — main —

print(“スクレイピング開始…”)
items = scrape_ranking()
print(f”{len(items)}件取得”)

for item in items:
print(f”詳細取得: {item[‘rank’]}位 {item[‘title’][:20]}”)
detail = scrape_detail(item[“url”])
item.update(detail)

ranking_data = {“date”: date_str, “date_key”: date_key, “items”: items}
tag_data = build_tag_ranking(items)

with open(RANKING_FILE, “w”, encoding=“utf-8”) as f:
json.dump(ranking_data, f, ensure_ascii=False, indent=2)

with open(TAG_FILE, “w”, encoding=“utf-8”) as f:
json.dump(tag_data, f, ensure_ascii=False, indent=2)

history = load_history()
history = save_history(history, ranking_data)

html = build_index_html(ranking_data, tag_data, history)
with open(INDEX_FILE, “w”, encoding=“utf-8”) as f:
f.write(html)

print(“完了！index.html生成済み”)
