import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

# --- ページ基本設定 ---
st.set_page_config(page_title="Garumani Tracker", layout="wide")

# --- デザイン：高級感、視認性、そして情報量のためのCSS ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@1,700&family=Material+Icons+Outlined" rel="stylesheet">
    
    <style>
    /* 全体の設定 */
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #fdfaf9; } /* シャンパンホワイト */
    
    /* 【超重要】StreamlitのデフォルトUI（ヘッダー、フッター、メインメニュー）を強制非表示 */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* アイコンの調整 */
    .material-icons-outlined { vertical-align: middle; font-size: 18px; color: #ff4d7d; margin-right: 5px;}

    /* ヘッダーセクション */
    .hero-container {
        text-align: center;
        padding: 40px 20px;
        background: white;
        border-bottom: 1px solid #f0e6e8;
        margin-bottom: 30px;
    }
    .hero-title {
        font-family: 'Playfair Display', serif;
        font-size: 2.8rem;
        color: #333333 !important; /* 濃いグレーにして視認性アップ */
        margin-bottom: 5px;
        letter-spacing: -1px;
    }
    .hero-subtitle {
        font-size: 0.8rem;
        color: #a0a0a0;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    /* アップデートボタン：洗練されたデザイン */
    div.stButton > button {
        background: #ff4d7d;
        color: white !important;
        border: none;
        border-radius: 4px;
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

    /* 作品カード：情報量を増やしつつスッキリさせる */
    .work-card {
        background: white;
        border-radius: 2px;
        padding: 25px;
        margin-bottom: 20px;
        border-left: 4px solid #ff4d7d; /* アクセントライン */
        display: flex;
        gap: 25px;
        align-items: flex-start; /* 上揃え */
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .rank-number {
        font-family: 'Playfair Display', serif;
        font-size: 2rem;
        font-style: italic;
        color: #ff4d7d;
        min-width: 40px;
        margin-top: -5px;
    }
    .work-image {
        width: 110px;
        height: 110px;
        object-fit: cover;
        border-radius: 2px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    .work-info h3 { 
        margin: 0 0 8px 0; 
        font-size: 1.15rem; 
        color: #333333 !important; /* 濃いグレーにして上品なフォントに */
        line-height: 1.4;
        font-family: 'Playfair Display', serif; /* 上品なフォント */
    }
    .work-circle { color: #888; font-size: 0.8rem; margin-bottom: 8px; }
    
    /* ジャンルタグ（チップスタイル） */
    .tag-container { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 10px; }
    .tag-badge {
        background: #fce4ec; /* 薄いピンク */
        color: #ff4d7d;
        font-size: 0.7rem;
        padding: 3px 8px;
        border-radius: 20px;
        font-weight: 700;
    }

    /* 値段とDL数 */
    .work-meta { font-size: 0.85rem; color: #555; }
    .work-meta-item { margin-bottom: 3px; display: flex; align-items: center; }
    .work-dl { font-weight: 700; color: #ff4d7d; font-size: 1.1rem; }
    
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

# --- データベース・詳細仕入れ処理 ---
# 情報量を増やしたので、DBファイル名を変更してスキーマを更新します
DB_NAME = "garumani_v_detailed.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # price（INTEGER）カラムを追加
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle_name TEXT, dl_count INTEGER, price INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
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
        
        # 様々なサイト構造に対応できるように網を広げる
        items = soup.select(".n_worklist_item") or soup.select(".work_1column")
        
        results = []
        now = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        
        for i, item in enumerate(items[:30], 1):
            try:
                title_tag = item.select_one(".work_name a") or item.select_one("dt a")
                title = title_tag.text.strip()
                circle = (item.select_one(".maker_name") or item.select_one(".circle_name")).text.strip()
                
                # DL数
                dl_text = item.text.replace(',', '')
                dl_match = re.search(r'(\d+)DL', dl_text)
                dl_count = int(dl_match.group(1)) if dl_match else 0
                
                # 値段 (新規取得)
                price_text = (item.select_one(".work_price") or item.select_one(".price")).text.replace(',', '')
                price = int(re.sub(r'\D', '', price_text)) if price_text else 0
                
                img = item.select_one("img")
                img_url = img.get('data-src') or img.get('src') or ""
                if img_url.startswith("//"): img_url = "https:" + img_url
                
                # ジャンルタグ (新規取得・詳細化)
                genre_tags = item.select(".work_category a") or item.select(".tag a")
                genres = ", ".join([g.text.strip() for g in genre_tags])
                
                results.append((i, title, circle, dl_count, price, genres, img_url, now))
            except: continue
        
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            # priceを含めて挿入
            c.executemany("INSERT INTO rankings VALUES (?,?,?,?,?,?,?,?)", results)
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
        if fetch_data():
            st.toast("Success!")
            st.rerun()

init_db()
conn = sqlite3.connect(DB_NAME)
# カラム名を明記して読み込む
df = pd.read_sql("SELECT rank, title, circle_name, dl_count, price, genres, thumbnail_url, updated_at FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    # 3. ジャンル分析（グラフも配色を洗練）
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.markdown("#### <span class='material-icons-outlined'>trending_up</span> Trend Analysis", unsafe_allow_html=True)
    all_genres = []
    # カンマ区切りのジャンルをバラバラにして集計
    for g in df['genres'].str.split(', '): all_genres.extend(g)
    g_df = pd.Series(all_genres).value_counts().head(8).reset_index()
    g_df.columns = ['Genre', 'Count']
    fig = px.bar(g_df, x='Count', y='Genre', orientation='h', 
                 color='Count', color_continuous_scale=['#fce4ec', '#ff4d7d'])
    fig.update_layout(height=300, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', 
                      margin=dict(l=0,r=0,t=20,b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # 4. ランキングリスト（情報量を大幅増加）
    st.markdown(f"#### <span class='material-icons-outlined'>list_alt</span> Daily Ranking / {df['updated_at'].iloc[0]}", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        # ジャンルタグをチップに変換
        tags_html = "".join([f'<span class="tag-badge">{tag}</span>' for tag in row['genres'].split(', ')])
        
        st.markdown(f"""
            <div class="work-card">
                <div class="rank-number">{row['rank']:02d}</div>
                <img src="{row['thumbnail_url']}" class="work-image">
                <div class="work-info">
                    <h3>{row['title']}</h3>
                    <div class="work-circle">{row['circle_name']}</div>
                    <div class="tag-container">{tags_html}</div>
                    <div class="work-meta">
                        <div class="work-meta-item">
                            <span class="material-icons-outlined">sell</span>
                            Price: ¥{row['price']:,}
                        </div>
                        <div class="work-meta-item">
                            <span class="material-icons-outlined">cloud_download</span>
                            <span class="work-dl">{row['dl_count']:,} DL</span>
                        </div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("No data available. Please click the update button.")
