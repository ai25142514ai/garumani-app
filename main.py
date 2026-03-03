import streamlit as st
import pandas as pd
import sqlite3
import requests
from bs4 import BeautifulSoup
import datetime
import re
import plotly.express as px

st.set_page_config(page_title="がるまに♡診断モード", layout="wide")

# デザイン設定
st.markdown("""
    <style>
    .stApp { background: #fffcfd; }
    .debug-box { background: #f0f2f6; padding: 10px; border-radius: 10px; font-family: monospace; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

DB_NAME = "garumani_debug.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rankings (rank INTEGER, title TEXT, circle_name TEXT, dl_count INTEGER, genres TEXT, thumbnail_url TEXT, updated_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def fetch_data():
    url = "https://www.dlsite.com/girls/ranking/day"
    # iPhoneからのアクセスをより忠実に再現
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja-jp",
        "Referer": "https://www.dlsite.com/"
    }
    
    try:
        res = requests.get(url, headers=headers, cookies={"adultchecked": "1"}, timeout=15)
        
        # 診断情報の表示
        st.info(f"診断情報: ステータスコード {res.status_code}")
        
        if res.status_code != 200:
            st.error(f"DLsiteから拒否されました (Error {res.status_code})。サーバーがブロックされている可能性があります。")
            return False

        soup = BeautifulSoup(res.content, "html.parser")
        items = soup.select(".n_worklist_item")
        
        if not items:
            st.warning("サイトは見えましたが、作品リストが見つかりません。サイトの構造が変わった可能性があります。")
            # 念のため中身を少し表示
            with st.expander("取得したページの内容を確認"):
                st.code(soup.prettify()[:1000])
            return False
            
        results = []
        now = datetime.datetime.now().strftime('%m/%d %H:%M')
        for i, item in enumerate(items[:30], 1):
            try:
                title = item.select_one(".work_name").text.strip()
                circle = item.select_one(".maker_name").text.strip()
                dl_text = item.select_one(".work_dl").text.replace(',', '')
                dl_count = int(re.search(r'\d+', dl_text).group()) if re.search(r'\d+', dl_text) else 0
                img = item.select_one(".work_thumb img")
                img_url = "https:" + (img.get('data-src') or img.get('src'))
                genres = ", ".join([a.text for a in item.select(".work_category a")])
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
    except Exception as e:
        st.error(f"通信エラーが発生しました: {e}")
    return False

# --- メイン画面 ---
st.title("🎀 がるまに♡診断中")

if st.button("🔍 データを仕入れてみる"):
    if fetch_data():
        st.success("成功しました！")
        st.rerun()

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM rankings ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    st.write(df)
else:
    st.write("現在、データは空っぽです。上のボタンを押して診断を開始してください。")
