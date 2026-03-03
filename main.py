import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="Garumani Analytics | Professional", layout="wide")

# --- プロ仕様の「重厚感」と「美しさ」を両立したCSS ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@0,700;1,700&family=Material+Icons+Outlined" rel="stylesheet">
    <style>
    /* 全体背景：単なる白ではなく、高級感のあるグレイッシュピンクの超微細グラデーション */
    .stApp {
        background: radial-gradient(circle at top left, #fffafb 0%, #f7f9fc 100%);
        font-family: 'Noto Sans JP', sans-serif;
        color: #2c3e50;
    }
    
    /* UIノイズの完全除去 */
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none !important; }

    /* タイトルエリア：ファッション誌の表紙のようなタイポグラフィ */
    .header-section {
        padding: 60px 0 40px 0;
        text-align: center;
        border-bottom: 1px solid #e1e8ed;
        margin-bottom: 50px;
        background: white;
    }
    .main-title {
        font-family: 'Playfair Display', serif;
        font-size: 4rem;
        font-weight: 700;
        color: #2c3e50 !important;
        margin: 0;
        letter-spacing: -2px;
    }
    .sub-title {
        font-size: 0.75rem;
        letter-spacing: 5px;
        color: #ff4d7d;
        font-weight: 700;
        text-transform: uppercase;
        margin-top: 10px;
    }

    /* 集計ボタン：プロのツールらしい重厚なデザイン */
    div.stButton > button {
        background: #2c3e50;
        color: white !important;
        border: none;
        border-radius: 0;
        padding: 18px 60px;
        font-weight: 700;
        letter-spacing: 3px;
        transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
        margin: 20px auto;
        display: block;
    }
    div.stButton > button:hover {
        background: #ff4d7d;
        transform: scale(1.02);
        box-shadow: 0 20px 40px rgba(255, 77, 125, 0.2);
    }

    /* 分析セクションのコンテナ */
    .analysis-card {
        background: white;
        padding: 40px;
        border: 1px solid #f0f3f5;
        box-shadow: 0 10px 30px rgba(0,0,0,0.02);
        margin-bottom: 50px;
    }

    /* 作品カード：プロのリストレイアウト */
    .work-card {
        background: white;
        padding: 30px;
        margin-bottom: 25px;
        display: flex;
        gap: 35px;
        align-items: flex-start;
        border: 1px solid #f0f3f5;
        transition: 0.3s ease;
        position: relative;
    }
    
    /* 10,000DL超えのネオン枠（大ヒット作への特別扱い） */
    .neon-frame {
        border: 2px solid #ff4d7d;
        box-shadow: 0 0 20px rgba(255, 77, 125, 0.4);
        background: linear-gradient(90deg, #ffffff 0%, #fff9fa 100%);
    }
    .neon-badge {
        position: absolute;
        top: -10px;
        right: 20px;
        background: #ff4d7d;
        color: white;
        padding: 4px 12px;
        font-size: 0.7rem;
        font-weight: 700;
        box-shadow: 0 5px 15px rgba(255, 77, 125, 0.4);
    }

    .rank-num {
        font-family: 'Playfair Display', serif;
        font-size: 3.5rem;
        font-style: italic;
        color: #f1f3f5;
        line-height: 1;
        min-width: 70px;
    }
    
    .work-thumb {
        width: 140px;
        height: 140px;
        object-fit: cover;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
    }

    .work-content { flex: 1; }
    .work-title {
        font-family: 'Playfair Display', serif;
        font-size: 1.5rem;
        font-weight: 700;
        color: #2c3e50 !important;
        line-height: 1.3;
        margin-bottom: 8px;
    }
    
    .circle-name { color: #95a5a6; font-size: 0.85rem; margin-bottom: 15px; }
    
    /* タグのデザイン */
    .tag-container { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 20px; }
    .tag-item {
        background: #f8f9fa;
        color: #5d6d7e;
        padding: 4px 14px;
        font-size: 0.7rem;
        font-weight: 700;
        border: 1px solid #edf2f7;
    }

    /* 数値情報：濃いグレーで見やすく */
    .metrics-box {
        display: flex;
        gap: 30px;
        padding-top: 15px;
        border-top: 1px solid #f1f3f5;
    }
    .metric-item { display: flex; flex-direction: column; }
    .metric-label { font-size: 0.65rem; color: #adb5bd; letter-spacing: 1px; margin-bottom: 3px; }
    .metric-value { font-family: 'Playfair Display', serif; font-size: 1.2rem; font-weight: 700; color: #2c3e50; }
    .dl-premium { color: #ff4d7d; }

    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_pro_v1.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data (rank INTEGER, title TEXT, circle TEXT, dl INTEGER, price INTEGER, genres TEXT, img TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
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
                
                raw_text = item.get_text().replace(',', '')
                dl_match = re.search(r'(\d+)DL', raw_text)
                dl = int(dl_match.group(1)) if dl_match else 0
                
                price_tag = item.select_one(".work_price") or item.select_one(".price")
                price = int(re.sub(r'\D', '', price_tag.get_text())) if price_tag else 0
                
                img = item.select_one("img").get('data-src') or item.select_one("img").get('src')
                if img.startswith("//"): img = "https:" + img
                
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = "|".join([g.get_text(strip=True) for g in genre_tags])
                
                results.append((i, title, circle, dl, price, genres, img, now))
            except: continue
        
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM data")
            c.executemany("INSERT INTO data VALUES (?,?,?,?,?,?,?,?)", results)
            conn.commit()
            conn.close()
            return True
    except: return False
    return False

# --- メインロジック ---
init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM data ORDER BY rank ASC", conn)
conn.close()

# 1. ヘッダー
st.markdown("""
    <div class="header-section">
        <h1 class="main-title">Garumani Analytics</h1>
        <div class="sub-title">Professional Market Insight</div>
    </div>
    """, unsafe_allow_html=True)

if st.button("RUN DATA AGGREGATOR"):
    with st.spinner("Aggregating market data..."):
        if fetch_data(): st.rerun()

if not df.empty:
    # 2. ジャンル占有率・マーケット分析
    st.markdown('<div class="analysis-card">', unsafe_allow_html=True)
    st.markdown("### <span class='material-icons-outlined'>donut_large</span> Market Genre Distribution", unsafe_allow_html=True)
    
    all_genres = []
    for gs in df['genres'].str.split('|'): all_genres.extend(gs)
    g_counts = pd.Series(all_genres).value_counts().head(12).reset_index()
    g_counts.columns = ['Genre', 'Count']
    
    fig = px.pie(g_counts, values='Count', names='Genre', hole=0.7, 
                 color_discrete_sequence=px.colors.sequential.RdPu_r)
    fig.update_layout(height=450, margin=dict(l=0,r=0,t=0,b=0), 
                      paper_bgcolor='rgba(0,0,0,0)', font=dict(family="Playfair Display", size=14))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 3. 集計レポート
    st.markdown(f"### <span class='material-icons-outlined'>article</span> Daily Report / {df['date'].iloc[0]}", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        is_hit = row['dl'] >= 10000
        neon_style = "neon-frame" if is_hit else ""
        badge_html = '<div class="neon-badge">10K+ HALL OF FAME</div>' if is_hit else ""
        tags_html = "".join([f'<span class="tag-item">{t}</span>' for t in row['genres'].split('|')])
        
        st.markdown(f"""
            <div class="work-card {neon_style}">
                {badge_html}
                <div class="rank-num">{row['rank']:02d}</div>
                <img src="{row['img']}" class="work-thumb">
                <div class="work-content">
                    <div class="work-title">{row['title']}</div>
                    <div class="circle-name">{row['circle']}</div>
                    <div class="tag-container">{tags_html}</div>
                    <div class="metrics-box">
                        <div class="metric-item">
                            <span class="metric-label">PRICE</span>
                            <span class="metric-value">¥{row['price']:,}</span>
                        </div>
                        <div class="metric-item">
                            <span class="metric-label">DOWNLOADS</span>
                            <span class="metric-value dl-premium">{row['dl']:,} DL</span>
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
else:
    st.info("集計システムは待機中です。中央のボタンを押して開始してください。")
