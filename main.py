import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- ページ設定 & デザイン ---
st.set_page_config(page_title="がるまに♡Tracker", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #fff0f3 0%, #ffffff 100%); }
    .cute-title { color: #ff4d7d; font-family: 'Hiragino Maru Gothic ProN', sans-serif; font-size: 2.2rem; font-weight: bold; text-align: center; margin: 20px 0 10px 0; }
    div.stButton > button { background: linear-gradient(90deg, #ff85a2, #ff4d7d); color: white; border: none; border-radius: 50px; padding: 0.8rem; font-size: 1.2rem; font-weight: bold; width: 100%; box-shadow: 0 4px 15px rgba(255, 120, 150, 0.4); }
    .top-card { background: white; border-radius: 25px; padding: 20px; border: 2px solid #ffccd9; box-shadow: 0 10px 25px rgba(255, 77, 125, 0.1); margin: 20px 0; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "ranking_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (id INTEGER PRIMARY KEY AUTOINCREMENT, rank INTEGER, product_id TEXT, title TEXT, circle_name TEXT, category TEXT, price INTEGER, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, scraped_at TIMESTAMP, UNIQUE(product_id, scraped_at))''')
    conn.commit()
    conn.close()

def run_scrape():
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1", "Referer": "https://www.dlsite.com/girls/"}
    cookies = {"adultchecked": "1"}
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        data_list = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        for i, item in enumerate(items, 1):
            try:
                name_tag = item.select_one(".work_name a")
                title = name_tag.text.strip()
                pid = re.search(r'(RJ\d+)', name_tag['href']).group(1)
                circle = (item.select_one(".maker_name") or item.select_one(".circle_name")).text.strip()
                price_text = (item.select_one(".work_price") or item.select_one(".price")).text
                price = int(re.sub(r'\D', '', price_text))
                img_tag = item.select_one("img")
                thumb_url = ""
                if img_tag:
                    thumb_url = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('data-original')
                    if thumb_url and thumb_url.startswith("//"): thumb_url = "https:" + thumb_url
                dl_text = item.text.replace(',', '')
                dl_match = re.search(r'([\d,]+)DL', dl_text)
                dl_count = int(dl_match.group(1)) if dl_match else 0
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = ", ".join([g.text.strip() for g in genre_tags]) if genre_tags else "がるまに"
                data_list.append((i, pid, title, circle, "Girls", price, dl_count, genres, thumb_url, now))
            except: continue
        if data_list:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings") 
            c.executemany('INSERT OR IGNORE INTO rankings (rank, product_id, title, circle_name, category, price, dl_count, genres, thumbnail_url, scraped_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_list)
            conn.commit()
            conn.close()
            return len(data_list)
    except: pass
    return 0

st.markdown('<p class="cute-title">🎀 がるまに♡Tracker</p>', unsafe_allow_html=True)

# ✨ ボタンを最上部に配置
if st.button("💖 最新ランキングにアップデート"):
    with st.spinner("魔法をかけています..."):
        count = run_scrape()
        if count > 0:
            st.toast("更新できたよ！")
            st.rerun()

st.divider()
init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    top = df.iloc[0]
    st.markdown(f"""
        <div class="top-card">
            <p style="color:#ff4d7d; font-weight:bold; font-size:1rem; margin-bottom:10px;">🏆 TODAY'S NO.1</p>
            <div style="display: flex; gap: 15px; align-items: flex-start;">
                <img src="{top['thumbnail_url']}" style="width:110px; border-radius:15px; border:1px solid #ffccd9;">
                <div>
                    <h3 style="margin:0; font-size:1.2rem; color:#333; line-height:1.4;">{top['title']}</h3>
                    <p style="margin:5px 0; color:#888; font-size:0.9rem;">サークル: {top['circle_name']}</p>
                    <p style="margin:5px 0; font-size:1.1rem; font-weight:bold; color:#ff4d7d;">📥 {top['dl_count']:,} DL</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    st.dataframe(df[['rank', 'thumbnail_url', 'title', 'circle_name', 'dl_count']], column_config={"thumbnail_url": st.column_config.ImageColumn("画像", width="small"), "rank": "位", "title": "作品名", "circle_name": "サークル", "dl_count": st.column_config.NumberColumn("DL数", format="%d 📥")}, hide_index=True, use_container_width=True)
else:
    st.info("上のボタンを押してね！")
