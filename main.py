import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re

# --- ページ設定 ---
st.set_page_config(page_title="がるまに♡Tracker", layout="wide")

# デザイン修正：文字を「絶対に見える濃い色」に固定
st.markdown("""
    <style>
    .main { background-color: #fffafb; }
    h1 { color: #ff4d7d !important; text-align: center; font-weight: 800; font-family: sans-serif; }

    /* カード内の文字色を強制的に黒系にする */
    .metric-card {
        background-color: white !important;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border: 2px solid #ffeef2;
        margin-bottom: 20px;
        color: #222 !important; 
    }
    .metric-card h2 { color: #333 !important; font-size: 1.3em !important; margin: 10px 0 !important; }
    .metric-card p { color: #444 !important; margin: 5px 0 !important; }
    .label-pink { color: #ff4d7d; font-weight: bold; }

    /* ボタン */
    .stButton>button {
        background-color: #ff85a2;
        color: white;
        border-radius: 20px;
        font-weight: bold;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "ranking_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS rankings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rank INTEGER, product_id TEXT, title TEXT, circle_name TEXT, 
            category TEXT, price INTEGER, dl_count INTEGER, genres TEXT, 
            thumbnail_url TEXT, scraped_at TIMESTAMP,
            UNIQUE(product_id, scraped_at)
        )
    ''')
    conn.commit()
    conn.close()

def run_scrape():
    # URLを「全年齢/R18両対応」のデイリー総合に変更
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.dlsite.com/girls/"
    }
    cookies = {"adultchecked": "1"}

    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")

        # 作品情報の取得（より確実なセレクタ）
        items = soup.select(".n_worklist_item")
        if not items:
            items = soup.find_all(class_=re.compile(r"work_1column|work_img_main"))

        data_list = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

        for i, item in enumerate(items, 1):
            try:
                # 1. 作品名とID
                name_tag = item.select_one(".work_name a")
                title = name_tag.text.strip()
                pid = re.search(r'(RJ\d+)', name_tag['href']).group(1)

                # 2. サークル名
                circle = item.select_one(".maker_name").text.strip()

                # 3. 価格（数字だけ抽出）
                price_text = item.select_one(".work_price").text
                price = int(re.sub(r'\D', '', price_text))

                # 4. 【重要】ダウンロード数（複数の場所を探す）
                dl_tag = item.select_one(".work_dl") or item.select_one(".dl_count") or item.select_one(".search_result_img_box_inner")
                dl_count = 0
                if dl_tag:
                    dl_match = re.search(r'([\d,]+)DL', dl_tag.text.replace(',', ''))
                    if dl_match:
                        dl_count = int(dl_match.group(1))
                    else:
                        # 数字だけのタグがある場合
                        dl_nums = re.findall(r'\d+', dl_tag.text.replace(',', ''))
                        if dl_nums: dl_count = int(dl_nums[0])

                # 5. 画像
                img_tag = item.select_one("img")
                thumb_url = ""
                if img_tag:
                    src = img_tag.get('data-src') or img_tag.get('src')
                    if src: thumb_url = "https:" + src if src.startswith("//") else src

                # 6. ジャンル
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = ", ".join([g.text.strip() for g in genre_tags]) if genre_tags else "Girls"

                data_list.append((i, pid, title, circle, "Girls", price, dl_count, genres, thumb_url, now))
            except: continue

        if data_list:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.executemany('INSERT OR IGNORE INTO rankings (rank, product_id, title, circle_name, category, price, dl_count, genres, thumbnail_url, scraped_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data_list)
            conn.commit()
            conn.close()
            return len(data_list)
    except: pass
    return 0

# --- アプリ表示 ---
st.markdown("<h1>🎀 がるまに♡Daily Tracker</h1>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### 🛠 メニュー")
    if st.button("✨ 最新データを取得"):
        # 取得前に古いデータをリセット（最新1回分にする）
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM rankings")
        conn.commit()
        conn.close()

        with st.spinner("DLsiteからデータを魔法で集めています..."):
            count = run_scrape()
            if count > 0:
                st.toast("更新に成功したよ！")
                st.rerun()

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    top = df.iloc[0]
    # NO.1 デザイン
    st.markdown(f"""
        <div class="metric-card">
            <span class="label-pink">TODAY'S NO.1 🏆</span>
            <div style="display: flex; gap: 15px; margin-top: 10px;">
                <img src="{top['thumbnail_url']}" style="width:100px; border-radius:10px; border:1px solid #eee;">
                <div>
                    <h2 style="margin:0;">{top['title']}</h2>
                    <p>サークル: {top['circle_name']}</p>
                    <p><span class="label-pink">📥 {top['dl_count']:,} DL</span> ／ 💰 {top['price']}円</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("### 💖 ランキング一覧")
    # テーブル表示
    st.dataframe(
        df[['rank', 'thumbnail_url', 'title', 'circle_name', 'dl_count', 'genres']],
        column_config={
            "thumbnail_url": st.column_config.ImageColumn("画像"),
            "rank": "位",
            "title": "作品タイトル",
            "circle_name": "サークル",
            "dl_count": st.column_config.NumberColumn("DL数", format="%d 📥"),
            "genres": "ジャンル"
        },
        hide_index=True,
        use_container_width=True
    )
else:
    st.info("左側のメニューから『最新データを取得』を押してね！")
