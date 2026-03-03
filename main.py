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

# --- 高級感のある「大人可愛い」デザイン ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; }
    .stApp { background: linear-gradient(135deg, #fffafa 0%, #ffffff 100%); }
    
    /* ヘッダー */
    .header-box {
        text-align: center;
        padding: 30px 0;
        background: linear-gradient(135deg, #ff758c 0%, #ff7eb3 100%);
        border-radius: 0 0 50px 50px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(255, 117, 140, 0.2);
    }
    .main-title { color: white; font-size: 2.5rem; font-weight: 800; margin: 0; }
    
    /* 1位の特別カード */
    .crown-card {
        background: white;
        border: 2px solid #ffd7e0;
        border-radius: 30px;
        padding: 25px;
        margin-bottom: 30px;
        box-shadow: 0 15px 40px rgba(255, 117, 140, 0.15);
        display: flex; gap: 25px; align-items: center;
    }
    
    /* ランキングアイテム */
    .rank-item {
        background: white;
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 15px;
        border: 1px solid #f0f0f0;
        display: flex; gap: 15px; align-items: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.02);
    }
    .rank-num {
        background: #ff758c; color: white; 
        min-width: 35px; height: 35px; border-radius: 10px;
        display: flex; align-items: center; justify-content: center; font-weight: bold;
    }
    
    /* ボタンを中央に、大きく */
    div.stButton > button {
        background: linear-gradient(90deg, #ff758c 0%, #ff7eb3 100%);
        color: white !important; border: none; border-radius: 50px;
        padding: 15px 30px; font-size: 1.2rem; font-weight: bold; width: 100%;
        box-shadow: 0 10px 20px rgba(255, 117, 140, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_v3.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, product_id TEXT, title TEXT, circle_name TEXT, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_dlsite_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"}
    cookies = {"adultchecked": "1"}
    
    try:
        response = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select(".n_worklist_item")
        
        data_list = []
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        
        for i, item in enumerate(items[:50], 1): # 上位50件
            title = item.select_one(".work_name a").text.strip()
            circle = item.select_one(".maker_name").text.strip()
            dl_text = item.select_one(".work_dl").text.replace(',', '')
            dl_count = int(re.search(r'\d+', dl_text).group()) if re.search(r'\d+', dl_text) else 0
            
            # 画像の取得を強化
            img_tag = item.select_one(".work_thumb img")
            img_url = img_tag.get('data-src') or img_tag.get('src')
            if img_url.startswith("//"): img_url = "https:" + img_url
            
            # ジャンル取得
            genre_tags = item.select(".work_category a")
            genres = ", ".join([g.text.strip() for g in genre_tags])
            
            data_list.append((i, "RJxxx", title, circle, dl_count, genres, img_url, now))
            
        if data_list:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM rankings")
            c.executemany("INSERT INTO rankings VALUES (?,?,?,?,?,?,?,?)", data_list)
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"エラーが発生しました: {e}")
    return False

# --- メインコンテンツ ---
st.markdown('<div class="header-box"><h1 class="main-title">🎀 がるまに♡Daily Tracker</h1></div>', unsafe_allow_html=True)

# 更新ボタン
if st.button("✨ DLsiteから最新データを仕入れる"):
    with st.spinner("DLsiteへ魔法をかけています..."):
        if fetch_dlsite_data():
            st.toast("仕入れ完了！最新の状態だよ♡")
            st.rerun()

st.write("---")

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    # 📊 ジャンル推移・分析セクション
    st.markdown("### 📈 人気ジャンル・トレンド (Top 50)")
    all_genres = []
    for g_str in df['genres'].dropna().str.split(', '):
        all_genres.extend(g_str)
    
    if all_genres:
        genre_counts = pd.Series(all_genres).value_counts().head(10).reset_index()
        genre_counts.columns = ['ジャンル', '作品数']
        fig = px.bar(genre_counts, x='作品数', y='ジャンル', orientation='h', 
                     color='作品数', color_continuous_scale='RdPu', text='作品数')
        fig.update_layout(height=350, paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig, use_container_width=True)

    # 👑 No.1 カード
    top = df.iloc[0]
    st.markdown(f"""
        <div class="crown-card">
            <img src="{top['thumbnail_url']}" style="width:140px; border-radius:20px; box-shadow: 0 8px 20px rgba(0,0,0,0.1);">
            <div>
                <span style="background:#ffd7e0; color:#ff4d7d; padding:4px 12px; border-radius:10px; font-weight:bold; font-size:0.8rem;">👑 第1位</span>
                <h2 style="margin:10px 0; font-size:1.4rem; color:#333;">{top['title']}</h2>
                <p style="margin:0; color:#666;">{top['circle_name']}</p>
                <p style="margin:10px 0; font-size:1.3rem; font-weight:bold; color:#ff4d7d;">📥 {top['dl_count']:,} DL</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 📋 ランキングリスト
    st.markdown("### 💖 デイリーランキング一覧")
    for _, row in df.iterrows():
        st.markdown(f"""
            <div class="rank-item">
                <div class="rank-num">{row['rank']}</div>
                <img src="{row['thumbnail_url']}" style="width:70px; height:70px; object-fit:cover; border-radius:10px;">
                <div style="flex:1;">
                    <div style="font-weight:bold; color:#444; font-size:1rem; line-height:1.3;">{row['title']}</div>
                    <div style="color:#888; font-size:0.8rem;">{row['circle_name']}</div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:5px;">
                        <span style="color:#ff758c; font-weight:bold;">{row['dl_count']:,} DL</span>
                        <span style="color:#bbb; font-size:0.7rem;">🏷️ {row['genres'].split(',')[0]}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
else:
    st.info("上のボタンを押して、記念すべき最初のデータを仕入れよう！")
