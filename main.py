import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- 1. ページ基本構成 ---
st.set_page_config(page_title="Garumani Analytics Pro", layout="wide")

# --- 2. プロ仕様のデザイン (CSS) ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@0,700;1,700&family=Material+Icons+Outlined" rel="stylesheet">
    <style>
    /* 全体のフォントと背景 */
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #1a1a1a !important; }
    .stApp { background-color: #fcf9f8; }
    
    /* UIノイズの完全除去 */
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none !important; }

    /* ヘッダーエリア */
    .header-container {
        text-align: center;
        padding: 60px 20px;
        background: white;
        border-bottom: 2px solid #1a1a1a;
        margin-bottom: 40px;
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        color: #1a1a1a !important; /* 超濃いグレー */
        letter-spacing: -2px;
        margin: 0;
    }
    .sub-brand {
        font-size: 0.8rem;
        letter-spacing: 4px;
        color: #ff4d7d;
        font-weight: 700;
        margin-top: 10px;
    }

    /* 集計ボタン */
    div.stButton > button {
        background: #1a1a1a;
        color: white !important;
        border: none;
        border-radius: 0;
        padding: 18px 60px;
        font-weight: 700;
        letter-spacing: 2px;
        transition: 0.4s;
        margin: 20px auto;
        display: block;
    }
    div.stButton > button:hover { background: #ff4d7d; transform: scale(1.02); }

    /* 分析セクション */
    .analysis-box {
        background: white;
        padding: 30px;
        border: 1px solid #eee;
        margin-bottom: 40px;
    }

    /* 作品カード：プロのレイアウト */
    .work-card {
        background: white;
        padding: 25px;
        margin-bottom: 20px;
        display: flex;
        gap: 25px;
        align-items: center;
        border: 1px solid #eee;
        position: relative;
    }
    
    /* 【目玉】10,000DL超えのネオン枠 */
    .neon-hit {
        border: 2px solid #ff4d7d !important;
        box-shadow: 0 0 15px rgba(255, 77, 125, 0.5);
        background: linear-gradient(90deg, #fff 0%, #fff9fa 100%);
    }
    .neon-label {
        position: absolute;
        top: -12px;
        right: 20px;
        background: #ff4d7d;
        color: white;
        padding: 2px 10px;
        font-size: 0.7rem;
        font-weight: 700;
        box-shadow: 0 4px 10px rgba(255, 77, 125, 0.3);
    }

    .rank-text {
        font-family: 'Playfair Display', serif;
        font-size: 3rem;
        font-style: italic;
        color: #e0e0e0;
        min-width: 60px;
    }
    .work-image { width: 110px; height: 110px; object-fit: cover; border: 1px solid #f0f0f0; }
    .work-content { flex: 1; }
    .work-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a1a1a !important;
        line-height: 1.4;
        margin-bottom: 8px;
    }
    
    .tag-container { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
    .tag-item {
        background: #f4f4f4;
        color: #666;
        padding: 3px 10px;
        font-size: 0.7rem;
        font-weight: 700;
    }
    
    .stats-row {
        display: flex;
        gap: 25px;
        font-size: 0.9rem;
        font-weight: 700;
        border-top: 1px solid #f0f0f0;
        padding-top: 12px;
        margin-top: 10px;
    }
    .dl-text { color: #ff4d7d; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_pro_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS report (rank INTEGER, title TEXT, circle TEXT, dl INTEGER, price INTEGER, genres TEXT, img TEXT, updated_at TEXT)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    # 超強力な擬装ヘッダー (iPhone 17相当)
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-jp"
    }
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        if res.status_code != 200: return False
        
        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        
        results = []
        now = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        
        for i, item in enumerate(items[:30], 1):
            try:
                title = (item.select_one(".work_name") or item.select_one("dt a")).get_text(strip=True)
                circle = (item.select_one(".maker_name") or item.select_one(".circle_name")).get_text(strip=True)
                
                # DL数抽出
                raw_text = item.get_text().replace(',', '')
                dl_match = re.search(r'(\d+)DL', raw_text)
                dl = int(dl_match.group(1)) if dl_match else 0
                
                # 値段抽出
                price_tag = item.select_one(".work_price") or item.select_one(".price")
                price = int(re.sub(r'\D', '', price_tag.get_text())) if price_tag else 0
                
                # 画像
                img_tag = item.select_one("img")
                img = img_tag.get('data-src') or img_tag.get('src')
                if img.startswith("//"): img = "https:" + img
                
                # ジャンル
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = "|".join([g.get_text(strip=True) for g in genre_tags])
                
                results.append((i, title, circle, dl, price, genres, img, now))
            except: continue
        
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM report")
            c.executemany("INSERT INTO report VALUES (?,?,?,?,?,?,?,?)", results)
            conn.commit()
            conn.close()
            return True
    except: return False
    return False

# --- 3. メイン表示部 ---
st.markdown("""
    <div class="header-container">
        <h1 class="main-title">Garumani Analytics</h1>
        <div class="sub-brand">Market Aggregation & Insight</div>
    </div>
    """, unsafe_allow_html=True)

if st.button("RUN AGGREGATOR"):
    with st.spinner("Fetching market data..."):
        if fetch_data(): st.rerun()

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM report ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    # ジャンル占有率分析
    st.markdown('<div class="analysis-box">', unsafe_allow_html=True)
    st.markdown("### <span class='material-icons-outlined'>pie_chart</span> Market Share by Genre", unsafe_allow_html=True)
    all_genres = []
    for gs in df['genres'].str.split('|'): all_genres.extend(gs)
    g_df = pd.Series(all_genres).value_counts().head(10).reset_index()
    g_df.columns = ['Genre', 'Count']
    fig = px.pie(g_df, values='Count', names='Genre', hole=0.6, color_discrete_sequence=px.colors.sequential.RdPu_r)
    fig.update_layout(height=400, margin=dict(l=10,r=10,t=10,b=10), paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ランキングレポート
    st.markdown(f"### <span class='material-icons-outlined'>insights</span> Daily Report / {df['updated_at'].iloc[0]}", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        is_hit = row['dl'] >= 10000
        hit_class = "neon-hit" if is_hit else ""
        badge = '<div class="neon-label">10K+ TRENDING</div>' if is_hit else ""
        tags = "".join([f'<span class="tag-item">{t}</span>' for t in row['genres'].split('|')])
        
        st.markdown(f"""
            <div class="work-card {hit_class}">
                {badge}
                <div class="rank-text">{row['rank']:02d}</div>
                <img src="{row['img']}" class="work-image">
                <div class="work-content">
                    <div class="work-title">{row['title']}</div>
                    <div style="color:#888; font-size:0.8rem;">{row['circle']}</div>
                    <div class="tag-container">{tags}</div>
                    <div class="stats-row">
                        <span>PRICE: ¥{row['price']:,}</span>
                        <span class="dl-text">TOTAL: {row['dl']:,} DL</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("集計システムを起動してください。")
