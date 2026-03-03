import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="Garumani Analytics Pro", layout="wide")

# --- プロフェッショナル・ダッシュボード CSS ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@0,700;1,700&family=Material+Icons+Outlined" rel="stylesheet">
    <style>
    /* 全体設定 */
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #2c3e50; }
    .stApp { background-color: #fdfaf9; }
    
    /* UIノイズの除去 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* ヘッダーエリア */
    .dashboard-header {
        text-align: left;
        padding: 40px 0;
        border-bottom: 2px solid #2c3e50;
        margin-bottom: 40px;
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        color: #2c3e50 !important;
        line-height: 1;
        margin: 0;
    }
    
    /* アップデートボタン */
    div.stButton > button {
        background: #2c3e50;
        color: white !important;
        border: none;
        border-radius: 0;
        padding: 15px 50px;
        font-weight: 700;
        letter-spacing: 2px;
        transition: 0.3s;
        margin: 20px 0;
    }
    div.stButton > button:hover { background: #ff4d7d; }

    /* 作品カード共通 */
    .work-card {
        background: white;
        padding: 25px;
        margin-bottom: 25px;
        display: flex;
        gap: 30px;
        align-items: center;
        transition: 0.3s;
        position: relative;
    }

    /* 【重要】10,000DL超えのネオン枠エフェクト */
    .neon-frame {
        border: 2px solid #ff4d7d;
        box-shadow: 0 0 15px #ff4d7d, inset 0 0 10px #ff4d7d;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 10px #ff4d7d; }
        50% { box-shadow: 0 0 25px #ff4d7d; }
        100% { box-shadow: 0 0 10px #ff4d7d; }
    }

    .rank-num {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-style: italic;
        color: #e0e0e0;
        min-width: 60px;
    }
    .work-image { width: 130px; height: 130px; object-fit: cover; border: 1px solid #eee; }
    .work-title { font-family: 'Playfair Display', serif; font-size: 1.4rem; font-weight: 700; color: #2c3e50 !important; margin-bottom: 10px; }
    
    /* タグのデザイン */
    .tag-box { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
    .tag { background: #f0f2f6; color: #5d6d7e; font-size: 0.75rem; padding: 4px 12px; font-weight: 700; }
    
    .price-dl-box { display: flex; gap: 20px; font-size: 0.9rem; font-weight: 700; }
    .dl-highlight { color: #ff4d7d; font-size: 1.2rem; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_analytics.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle TEXT, dl INTEGER, price INTEGER, genres TEXT, img TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    # より強力な擬装ヘッダー
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        
        results = []
        now = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        
        for i, item in enumerate(items[:30], 1):
            try:
                title = (item.select_one(".work_name") or item.select_one("dt a")).get_text(strip=True)
                circle = (item.select_one(".maker_name") or item.select_one(".circle_name")).get_text(strip=True)
                
                # 数値データの抽出
                raw_text = item.get_text().replace(',', '')
                dl_match = re.search(r'(\d+)DL', raw_text)
                dl = int(dl_match.group(1)) if dl_match else 0
                
                price_text = (item.select_one(".work_price") or item.select_one(".price")).get_text(strip=True)
                price = int(re.sub(r'\D', '', price_text)) if price_text else 0
                
                img = item.select_one("img").get('data-src') or item.select_one("img").get('src')
                if img.startswith("//"): img = "https:" + img
                
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = "|".join([g.get_text(strip=True) for g in genre_tags])
                
                results.append((i, title, circle, dl, price, genres, img, now))
            except: continue
        
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            c.executemany("INSERT INTO rankings VALUES (?,?,?,?,?,?,?,?)", results)
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

# 1. ヘッダー
st.markdown(f"""
    <div class="dashboard-header">
        <p style="letter-spacing:4px; font-size:0.8rem; margin:0; color:#888;">MARKET DATA AGGREGATION</p>
        <h1 class="main-title">Garumani Analytics</h1>
    </div>
    """, unsafe_allow_html=True)

if st.button("RUN DATA AGGREGATOR"):
    if fetch_data(): st.rerun()

if not df.empty:
    # 2. ジャンル推移・占有率分析
    st.markdown("### <span class='material-icons-outlined'>donut_large</span> Market Genre Share", unsafe_allow_html=True)
    all_genres = []
    for gs in df['genres'].str.split('|'): all_genres.extend(gs)
    g_counts = pd.Series(all_genres).value_counts().head(10).reset_index()
    g_counts.columns = ['Genre', 'Count']
    
    fig = px.pie(g_counts, values='Count', names='Genre', hole=0.6, 
                 color_discrete_sequence=px.colors.sequential.RdPu_r)
    fig.update_layout(height=400, margin=dict(l=0,r=0,t=0,b=0))
    st.plotly_chart(fig, use_container_width=True)

    # 3. 集計リスト
    st.markdown(f"### <span class='material-icons-outlined'>analytics</span> Insights Report / {df['date'].iloc[0]}", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        # 10,000DL超え判定
        neon_class = "neon-frame" if row['dl'] >= 10000 else ""
        tags_html = "".join([f'<span class="tag">{t}</span>' for t in row['genres'].split('|')])
        
        st.markdown(f"""
            <div class="work-card {neon_class}">
                <div class="rank-num">{row['rank']:02d}</div>
                <img src="{row['img']}" class="work-image">
                <div style="flex:1;">
                    <div class="work-title">{row['title']}</div>
                    <div style="color:#888; font-size:0.85rem;">{row['circle']}</div>
                    <div class="tag-box">{tags_html}</div>
                    <div class="price-dl-box">
                        <span>PRICE: ¥{row['price']:,}</span>
                        <span class="dl-highlight">TOTAL: {row['dl']:,} DL</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("集計システムを起動してください。")
