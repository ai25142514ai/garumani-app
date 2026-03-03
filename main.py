import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="がるまに♡Tracker Pro", layout="wide")

# --- 画像を参考にした「シンプル＆スタイリッシュ」CSS ---
st.markdown("""
    <style>
    /* フォント設定と背景色 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
    .stApp { background: #fffcfd; }
    
    /* 全体の文字色を濃いグレーに固定（見にくさを解消） */
    h1, h2, h3, h4, h5, p, span, div, li, ul { color: #333333; }
    
    /* タイトルのデザイン（画像1の雰囲気を再現） */
    .cute-title { 
        color: #ff4d7d; 
        font-size: 2.2rem; 
        font-weight: 800; 
        text-align: center; 
        margin-bottom: 0.2rem;
    }
    .last-updated {
        color: #888888;
        text-align: center;
        font-size: 0.8rem;
        margin-bottom: 1.5rem;
    }
    
    /* 更新ボタン：ピンクのグラデーション、丸角（画像1を忠実に再現） */
    div.stButton > button {
        background: linear-gradient(90deg, #ff80a0 0%, #ff4d7d 100%);
        color: white;
        border: none;
        border-radius: 50px;
        font-weight: bold;
        width: 100%;
        height: 3.2rem;
        box-shadow: 0 8px 20px rgba(255, 77, 125, 0.3);
        transition: 0.3s;
        font-size: 1.1rem;
    }
    div.stButton > button:hover { transform: translateY(-3px); box-shadow: 0 12px 25px rgba(255, 77, 125, 0.4); }

    /* 作品カード：浮かび上がるような丸角（画像1のレイアウト） */
    .work-card {
        background: white;
        border-radius: 20px;
        padding: 18px;
        margin-bottom: 15px;
        border: 1px solid #ffeef2;
        display: flex;
        gap: 18px;
        align-items: center;
        box-shadow: 0 6px 18px rgba(255, 117, 140, 0.08);
    }
    /* 順位バッジ：ピンク背景、白抜き文字 */
    .rank-badge {
        background: #ff4d7d;
        color: white;
        min-width: 35px;
        height: 35px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        font-size: 1.1rem;
    }
    /* DL数：太字、ピンク */
    .dl-count {
        color: #ff4d7d;
        font-weight: bold;
        font-size: 1.2rem;
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_final_styling.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle_name TEXT, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    # 前回の診断で成功したheadersを使用
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        
        results = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for i, item in enumerate(items[:30], 1): # 上位30件
            try:
                title_tag = item.select_one(".work_name a") or item.select_one("dt a")
                title = title_tag.text.strip()
                circle = (item.select_one(".maker_name") or item.select_one(".circle_name")).text.strip()
                dl_text = item.text.replace(',', '')
                dl_match = re.search(r'(\d+)DL', dl_text)
                dl_count = int(dl_match.group(1)) if dl_match else 0
                img = item.select_one("img")
                img_url = img.get('data-src') or img.get('src') or ""
                if img_url.startswith("//"): img_url = "https:" + img_url
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = ", ".join([g.text.strip() for g in genre_tags])
                results.append((i, title, circle, dl_count, genres, img_url, now))
            except: continue
        
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            c.executemany("INSERT INTO rankings VALUES (?,?,?,?,?,?,?)", results)
            conn.commit()
            conn.close()
            return True
    except: return False
    return False

# --- メインロジック ---
init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

# アプリヘッダー（画像にある最終更新日時を追加）
st.markdown('<div class="cute-title">🎀 がるまに♡Tracker Pro</div>', unsafe_allow_html=True)
if not df.empty:
    st.markdown(f'<div class="last-updated">最終更新: {df["updated_at"].iloc[0]}</div>', unsafe_allow_html=True)
else:
    st.markdown(f'<div class="last-updated">まだデータがありません。下のボタンを押して仕入れよう！</div>', unsafe_allow_html=True)

# アクション：ピンクのグラデーションボタン
if st.button("✨ 最新ランキングにアップデート"):
    with st.spinner("DLsiteから魔法をかけています..."):
        if fetch_data():
            st.toast("仕入れ完了！最新の状態だよ♡")
            st.rerun()

st.divider()

if not df.empty:
    # 📊 ジャンル推移・分析グラフ（スタイリッシュで情報量が多いので維持）
    st.markdown("### 📊 人気ジャンルトレンド (Top 30)")
    all_genres = []
    for g_str in df['genres'].dropna().str.split(', '):
        all_genres.extend(g_str)
    
    if all_genres:
        genre_counts = pd.Series(all_genres).value_counts().head(8).reset_index()
        genre_counts.columns = ['ジャンル', '作品数']
        fig = px.bar(genre_counts, x='作品数', y='ジャンル', orientation='h', 
                     color='作品数', color_continuous_scale='RdPu', text='作品数')
        fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    # 🏆 ランキング（画像にあるカード型レイアウトを忠実に再現）
    st.markdown("### 🏆 今日のデイリーランキング")
    for _, row in df.iterrows():
        st.markdown(f"""
            <div class="work-card">
                <div class="rank-badge">{row['rank']}</div>
                <img src="{row['thumbnail_url']}" style="width:100px; height:100px; object-fit:cover; border-radius:15px; border:1px solid #ffccd9;">
                <div style="flex:1;">
                    <div style="font-weight:bold; font-size:1.05rem; line-height:1.4;">{row['title']}</div>
                    <div style="color:#666666; font-size:0.85rem; margin-top:3px;">サークル: {row['circle_name']}</div>
                    <div class="dl-count">📥 {row['dl_count']:,} DL</div>
                </div>
            </div>
        """, unsafe_allow_html=True)
