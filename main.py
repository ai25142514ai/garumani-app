import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="がるまに Tracker Pro", layout="wide")

# --- デザイン：標準絵文字を廃止し、Googleアイコンと洗練されたフォントを採用 ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@1,700&family=Material+Icons+Outlined" rel="stylesheet">
    
    <style>
    /* 全体の設定 */
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #fdfaf9; } /* 柔らかなシャンパンホワイト */
    
    /* 標準の絵文字を非表示にしたい場合やアイコンの調整 */
    .material-icons-outlined { vertical-align: middle; font-size: 20px; color: #ff4d7d; }

    /* ヘッダーセクション */
    .hero-container {
        text-align: center;
        padding: 50px 20px;
        background: white;
        border-bottom: 1px solid #f0e6e8;
        margin-bottom: 40px;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        color: #ff4d7d;
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 0.9rem;
        color: #a0a0a0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* アップデートボタン：絵文字なし・洗練されたデザイン */
    div.stButton > button {
        background: #ff4d7d;
        color: white !important;
        border: none;
        border-radius: 4px; /* 丸すぎず少し角を残すスタイリッシュさ */
        padding: 12px 40px;
        font-weight: 400;
        letter-spacing: 1px;
        transition: 0.4s;
        width: auto;
        display: block;
        margin: 0 auto;
        box-shadow: 0 4px 15px rgba(255, 77, 125, 0.2);
    }
    div.stButton > button:hover {
        background: #e03e68;
        box-shadow: 0 6px 20px rgba(255, 77, 125, 0.3);
    }

    /* 作品カード：参考画像のような清潔感のあるカード */
    .work-card {
        background: white;
        border-radius: 2px; /* 直線的な美しさ */
        padding: 25px;
        margin-bottom: 20px;
        border-left: 4px solid #ff4d7d; /* アクセントライン */
        display: flex;
        gap: 25px;
        align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .rank-number {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-style: italic;
        color: #ff4d7d;
        min-width: 40px;
    }
    .work-image {
        width: 120px;
        height: 120px;
        object-fit: cover;
        border-radius: 2px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .work-info h3 { margin: 0; font-size: 1.2rem; color: #333; line-height: 1.4; }
    .work-circle { color: #888; font-size: 0.85rem; margin-top: 5px; }
    .work-stats { margin-top: 15px; font-weight: 700; color: #ff4d7d; font-size: 1.1rem; }
    
    /* グラフの枠 */
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 2px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        margin-bottom: 40px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- データベース・仕入れ処理 (前回と同じですが改善済) ---
DB_NAME = "garumani_vfinal.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle_name TEXT, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        results = []
        now = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        for i, item in enumerate(items[:30], 1):
            title = item.select_one(".work_name").text.strip()
            circle = item.select_one(".maker_name").text.strip()
            dl_text = item.text.replace(',', '')
            dl_match = re.search(r'(\d+)DL', dl_text)
            dl_count = int(dl_match.group(1)) if dl_match else 0
            img = item.select_one("img")
            img_url = "https:" + (img.get('data-src') or img.get('src') or "")
            genres = ", ".join([a.text for a in item.select(".work_category a")])
            results.append((i, title, circle, dl_count, genres, img_url, now))
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

# --- メイン画面の表示 ---

# 1. ヘッダー
st.markdown("""
    <div class="hero-container">
        <div class="hero-subtitle">Analytics & Insights</div>
        <h1 class="hero-title">Garumani Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

# 2. アップデートボタン
if st.button("UPDATE LATEST DATA"):
    with st.spinner("Fetching..."):
        if fetch_data(): st.rerun()

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    # 3. ジャンル分析（グラフも配色を洗練）
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("#### <span class='material-icons-outlined'>trending_up</span> Trend Analysis", unsafe_allow_html=True)
    all_genres = []
    for g in df['genres'].str.split(', '): all_genres.extend(g)
    g_df = pd.Series(all_genres).value_counts().head(8).reset_index()
    g_df.columns = ['Genre', 'Count']
    fig = px.bar(g_df, x='Count', y='Genre', orientation='h', 
                 color='Count', color_continuous_scale=['#fce4ec', '#ff4d7d'])
    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      margin=dict(l=0,r=0,t=20,b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. ランキングリスト
    st.markdown(f"#### <span class='material-icons-outlined'>list_alt</span> Daily Ranking / {df['updated_at'].iloc[0]}", unsafe_allow_html=True)
    for _, row in df.iterrows():
        st.markdown(f"""
            <div class="work-card">
                <div class="rank-number">{row['rank']:02d}</div>
                <img src="{row['thumbnail_url']}" class="work-image">
                <div class="work-info">
                    <h3>{row['title']}</h3>
                    <div class="work-circle">{row['circle_name']}</div>
                    <div class="work-stats">{row['dl_count']:,} <span style="font-size:0.8rem; font-weight:400;">DL</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("No data available. Please click the update button above.")
