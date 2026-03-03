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

# --- 高級感のあるCSS（Material Iconsを使用） ---
st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@300;400;700&family=Playfair+Display:ital,wght@1,700&family=Material+Icons+Outlined" rel="stylesheet">
    <style>
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #4A4A4A; }
    .stApp { background-color: #fdfaf9; }
    .hero-container { text-align: center; padding: 40px 20px; background: white; border-bottom: 1px solid #f0e6e8; margin-bottom: 30px; }
    .hero-title { font-family: 'Playfair Display', serif; font-size: 2.8rem; color: #ff4d7d; margin-bottom: 5px; }
    .hero-subtitle { font-size: 0.8rem; color: #a0a0a0; letter-spacing: 2px; text-transform: uppercase; }
    div.stButton > button {
        background: #ff4d7d; color: white !important; border: none; border-radius: 4px;
        padding: 12px 40px; font-weight: 400; letter-spacing: 1px; width: auto; display: block; margin: 0 auto;
        box-shadow: 0 4px 15px rgba(255, 77, 125, 0.2);
    }
    .work-card {
        background: white; border-radius: 2px; padding: 20px; margin-bottom: 15px;
        border-left: 4px solid #ff4d7d; display: flex; gap: 20px; align-items: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.03);
    }
    .rank-number { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-style: italic; color: #ff4d7d; min-width: 40px; }
    .work-image { width: 100px; height: 100px; object-fit: cover; border-radius: 2px; }
    .work-stats { margin-top: 10px; font-weight: 700; color: #ff4d7d; font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_v_stable.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle_name TEXT, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_data():
    # 女性向けデイリーランキング
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.dlsite.com/"
    }
    
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        soup = BeautifulSoup(res.content, "html.parser")
        
        # 【重要】複数のセレクターを試す「網」の強化
        items = soup.find_all(class_=re.compile(r"worklist_item|work_1column|item_list"))
        
        # もし上記で見つからない場合、もっと原始的に探す
        if not items:
            items = soup.select('tr') or soup.select('li')
            
        results = []
        now = datetime.datetime.now().strftime('%Y.%m.%d %H:%M')
        
        count = 1
        for item in items:
            if count > 30: break # 上位30件
            
            # 作品名を探す
            title_tag = item.select_one('.work_name') or item.find('a', class_=re.compile(r'name'))
            if not title_tag: continue
            title = title_tag.text.strip()
            
            # サークル名
            circle_tag = item.select_one('.maker_name') or item.select_one('.circle_name')
            circle = circle_tag.text.strip() if circle_tag else "Unknown Circle"
            
            # DL数
            dl_text = item.get_text().replace(',', '')
            dl_match = re.search(r'(\d+)DL', dl_text)
            dl_count = int(dl_match.group(1)) if dl_match else 0
            
            # 画像
            img = item.select_one('img')
            img_url = ""
            if img:
                img_url = img.get('data-src') or img.get('src') or ""
                if img_url.startswith("//"): img_url = "https:" + img_url
            
            # ジャンル
            genre_tags = item.select('.work_category a') or item.select('.tag a')
            genres = ", ".join([g.text.strip() for g in genre_tags]) if genre_tags else "Girls"
            
            results.append((count, title, circle, dl_count, genres, img_url, now))
            count += 1
            
        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            c.executemany("INSERT INTO rankings VALUES (?,?,?,?,?,?,?)", results)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Error: {e}")
    return False

# --- メイン画面 ---
st.markdown("""
    <div class="hero-container">
        <div class="hero-subtitle">Premium Analytics</div>
        <h1 class="hero-title">Garumani Tracker</h1>
    </div>
    """, unsafe_allow_html=True)

if st.button("UPDATE LATEST DATA"):
    with st.spinner("Accessing DLsite..."):
        if fetch_data():
            st.success("SUCCESS")
            st.rerun()
        else:
            st.warning("Data found: 0. サイト構造が変更された可能性があります。")

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    # トレンド分析（グラフ）
    st.markdown("#### <span class='material-icons-outlined'>bar_chart</span> Trend Analysis", unsafe_allow_html=True)
    all_genres = []
    for g in df['genres'].str.split(', '): all_genres.extend(g)
    g_df = pd.Series(all_genres).value_counts().head(8).reset_index()
    g_df.columns = ['Genre', 'Count']
    fig = px.bar(g_df, x='Count', y='Genre', orientation='h', color='Count', color_continuous_scale=['#fce4ec', '#ff4d7d'])
    fig.update_layout(height=250, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=20,b=0), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # ランキングリスト
    st.markdown(f"#### <span class='material-icons-outlined'>format_list_numbered</span> Daily Ranking / {df['updated_at'].iloc[0]}", unsafe_allow_html=True)
    for _, row in df.iterrows():
        st.markdown(f"""
            <div class="work-card">
                <div class="rank-number">{row['rank']:02d}</div>
                <img src="{row['thumbnail_url']}" class="work-image">
                <div class="work-info">
                    <div style="font-weight:700; font-size:1rem; line-height:1.4;">{row['title']}</div>
                    <div style="color:#888; font-size:0.8rem; margin-top:4px;">{row['circle_name']}</div>
                    <div class="work-stats">{row['dl_count']:,} <span style="font-size:0.7rem; font-weight:400;">DL</span></div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("No data available. Please click the update button.")
