import streamlit as st
import pandas as pd
import sqlite3
import requests
import datetime
import xml.etree.ElementTree as ET
import re

st.set_page_config(page_title="Garumani Analytics Pro", layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Playfair+Display:ital,wght@1,700" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #1a1a1a !important; }
    .stApp { background-color: #fcf9f8; }
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none !important; }
    .header-box { text-align: center; padding: 50px 0; background: white; border-bottom: 2px solid #1a1a1a; margin-bottom: 30px; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3.2rem; color: #1a1a1a !important; margin: 0; }
    div.stButton > button { background: #1a1a1a; color: white !important; border: none; border-radius: 0; padding: 15px; font-weight: 700; width: 100%; transition: 0.3s; }
    div.stButton > button:hover { background: #ff4d7d; }
    .work-card { background: white; padding: 25px; margin-bottom: 20px; display: flex; gap: 20px; align-items: flex-start; border: 1px solid #eee; position: relative; }
    .neon-hit { border: 2px solid #ff4d7d !important; box-shadow: 0 0 15px rgba(255, 77, 125, 0.4); }
    .neon-label { position: absolute; top: -12px; right: 20px; background: #ff4d7d; color: white; padding: 2px 10px; font-size: 0.7rem; font-weight: 700; }
    .rank-text { font-family: 'Playfair Display', serif; font-size: 2.8rem; font-style: italic; color: #d0d0d0; min-width: 60px; }
    .work-image { width: 110px; height: 110px; object-fit: cover; border: 1px solid #f0f0f0; flex-shrink: 0; }
    .work-title { font-family: 'Playfair Display', serif; font-size: 1.25rem; font-weight: 700; color: #1a1a1a !important; margin-bottom: 5px; }
    .tag-container { display: flex; flex-wrap: wrap; gap: 5px; margin: 8px 0; }
    .tag-item { background: #f4f4f4; color: #666; padding: 2px 8px; font-size: 0.65rem; font-weight: 700; }
    .stats-row { display: flex; gap: 25px; font-size: 0.9rem; font-weight: 700; border-top: 1px solid #f0f0f0; padding-top: 12px; margin-top: 10px; }
    .dl-text { color: #ff4d7d; font-size: 1.1rem; }
</style>
""", unsafe_allow_html=True)

DB_NAME = "garumani_v_final_secure.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS data (rank INTEGER, title TEXT, circle TEXT, dl INTEGER, price INTEGER, genres TEXT, img TEXT, date TEXT)")
    conn.commit()
    conn.close()

def fetch_data():
    # DLsite がるまに RSS（ランキング上位作品）
    url = "https://www.dlsite.com/girls/ranking/day/type/SOU/lang/jp.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        st.write(f"HTTPステータス: {res.status_code}")
        st.write(f"レスポンスサイズ: {len(res.content)} bytes")

        if res.status_code != 200 or len(res.content) < 100:
            st.error("データ取得に失敗しました。レスポンス内容を確認します。")
            st.code(res.text[:2000])
            return False

        root = ET.fromstring(res.content)
        ns = {"content": "http://purl.org/rss/1.0/modules/content/"}

        items = root.findall(".//item")
        st.write(f"RSS アイテム数: {len(items)}件")

        if not items:
            st.warning("アイテムが見つかりませんでした。")
            st.code(res.text[:3000])
            return False

        results = []
        now = datetime.datetime.now().strftime("%Y.%m.%d %H:%M")

        for i, item in enumerate(items[:30], 1):
            try:
                title = item.findtext("title") or "不明"
                link = item.findtext("link") or ""

                # 説明文からサークル名・価格・DL数を抽出
                desc = item.findtext("description") or ""

                # 画像URL取得
                img = ""
                enclosure = item.find("enclosure")
                if enclosure is not None:
                    img = enclosure.get("url", "")

                # 説明からテキスト抽出
                clean_desc = re.sub(r"<[^>]+>", "", desc)

                circle_match = re.search(r"サークル名[：:]\s*(.+?)[\n\r]", clean_desc)
                circle = circle_match.group(1).strip() if circle_match else "不明"

                price_match = re.search(r"(\d[\d,]+)円", clean_desc)
                price = int(price_match.group(1).replace(",", "")) if price_match else 0

                dl_match = re.search(r"([\d,]+)\s*DL", clean_desc)
                dl = int(dl_match.group(1).replace(",", "")) if dl_match else 0

                genres = ""
                results.append((i, title, circle, dl, price, genres, img, now))

            except Exception as e:
                st.warning(f"行{i} スキップ: {e}")
                continue

        st.write(f"処理完了: {len(results)}件")

        if results:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("DELETE FROM data")
            c.executemany("INSERT INTO data VALUES (?,?,?,?,?,?,?,?)", results)
            conn.commit()
            conn.close()
            return True

    except Exception as e:
        st.error(f"全体エラー: {e}")
        return False

    return False

# ヘッダー
st.markdown('<div class="header-box"><h1 class="main-title">Garumani Analytics</h1><div style="color:#ff4d7d;font-weight:bold;letter-spacing:2px;font-size:0.7rem;">MARKET DATA AGGREGATOR</div></div>', unsafe_allow_html=True)

if st.button("RUN DATA AGGREGATOR"):
    with st.spinner("Aggregating market data..."):
        if fetch_data():
            st.success("集計完了！")
            st.rerun()
        else:
            st.error("集計に失敗しました。上の情報を確認してください。")

init_db()
conn = sqlite3.connect(DB_NAME)
df = pd.read_sql("SELECT * FROM data ORDER BY rank ASC", conn)
conn.close()

if not df.empty:
    try:
        import plotly.express as px
        all_genres = []
        for gs in df["genres"].dropna().str.split("|"):
            all_genres.extend([g for g in gs if g])
        if all_genres:
            g_df = pd.Series(all_genres).value_counts().head(10).reset_index()
            g_df.columns = ["Genre", "Count"]
            fig = px.pie(g_df, values="Count", names="Genre", hole=0.6,
                         color_discrete_sequence=px.colors.sequential.RdPu_r)
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20),
                              paper_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, width="stretch")
    except Exception as e:
        st.warning(f"グラフ表示エラー: {e}")

    for _, row in df.iterrows():
        hit = "neon-hit" if row["dl"] >= 10000 else ""
        badge = '<div class="neon-label">10K+ TRENDING</div>' if row["dl"] >= 10000 else ""
        tags = "".join([f'<span class="tag-item">{t}</span>' for t in str(row["genres"]).split("|") if t])
        st.markdown(
            f'<div class="work-card {hit}">{badge}'
            f'<div class="rank-text">{row["rank"]:02d}</div>'
            f'<img src="{row["img"]}" class="work-image">'
            f'<div style="flex:1;">'
            f'<div class="work-title">{row["title"]}</div>'
            f'<div style="color:#888;font-size:0.8rem;">{row["circle"]}</div>'
            f'<div class="tag-container">{tags}</div>'
            f'<div class="stats-row"><span>PRICE: ¥{row["price"]:,}</span>'
            f'<span class="dl-text">TOTAL: {row["dl"]:,} DL</span></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )
else:
    st.info("集計システムを起動してください。「RUN DATA AGGREGATOR」ボタンを押してください。")
