import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Garumani Analytics Pro", layout="wide")

st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700&family=Playfair+Display:ital,wght@1,700" rel="stylesheet">
<style>
    html, body, [class*="css"] { font-family: 'Noto Sans JP', sans-serif; color: #1a1a1a !important; }
    .stApp { background-color: #fcf9f8; }
    #MainMenu, header, footer, .stDeployButton { visibility: hidden; display: none !important; }
    .header-box { text-align: center; padding: 50px 0; background: white; border-bottom: 2px solid #1a1a1a; margin-bottom: 30px; }
    .main-title { font-family: 'Playfair Display', serif; font-size: 3.2rem; color: #1a1a1a !important; margin: 0; }
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

st.markdown('<div class="header-box"><h1 class="main-title">Garumani Analytics</h1><div style="color:#ff4d7d;font-weight:bold;letter-spacing:2px;font-size:0.7rem;">MARKET DATA AGGREGATOR</div></div>', unsafe_allow_html=True)

# GitHubから直接CSVを読み込む
CSV_URL = "https://raw.githubusercontent.com/ai25142514ai/garumani-app/main/ranking.csv"

try:
    df = pd.read_csv(CSV_URL)
except Exception as e:
    df = pd.DataFrame()
    st.warning(f"データ読み込みエラー: {e}")

if not df.empty:
    if "date" in df.columns and len(df) > 0:
        st.markdown(f'<div style="text-align:center;color:#888;font-size:0.8rem;margin-bottom:20px;">最終更新: {df["date"].iloc[0]}</div>', unsafe_allow_html=True)

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
        dl = int(row["dl"]) if str(row["dl"]).isdigit() else 0
        hit = "neon-hit" if dl >= 10000 else ""
        badge = '<div class="neon-label">10K+ TRENDING</div>' if dl >= 10000 else ""
        tags = "".join([f'<span class="tag-item">{t}</span>' for t in str(row["genres"]).split("|") if t])
        price = int(row["price"]) if str(row["price"]).isdigit() else 0
        st.markdown(
            f'<div class="work-card {hit}">{badge}'
            f'<div class="rank-text">{int(row["rank"]):02d}</div>'
            f'<img src="{row["img"]}" class="work-image">'
            f'<div style="flex:1;">'
            f'<div class="work-title">{row["title"]}</div>'
            f'<div style="color:#888;font-size:0.8rem;">{row["circle"]}</div>'
            f'<div class="tag-container">{tags}</div>'
            f'<div class="stats-row"><span>PRICE: ¥{price:,}</span>'
            f'<span class="dl-text">TOTAL: {dl:,} DL</span></div>'
            f'</div></div>',
            unsafe_allow_html=True
        )
else:
    st.info("データを準備中です。しばらくお待ちください。（毎朝10時頃に自動更新されます）")
