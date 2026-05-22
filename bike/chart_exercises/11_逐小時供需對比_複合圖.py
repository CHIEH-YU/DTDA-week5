# ============================================================
# 練習 11 ── 逐小時供需對比（Bar + Line 複合圖）
# ============================================================
# 學習重點：
#   1. make_subplots(secondary_y=True) 建立雙 Y 軸畫布
#   2. 在同一張圖混用 go.Bar（長條）和 go.Scatter（折線）
#   3. fig.update_yaxes 分別設定兩條 y 軸的標題
# 執行：streamlit run 11_逐小時供需對比_複合圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="練習 11｜逐小時供需", layout="wide")
st.title("練習 11｜逐小時供需對比（Bar + Line 複合圖）")
st.caption("資料來源：available_cars.csv + orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
available_cars = pd.read_csv(str(DATA_DIR / "available_cars.csv"))
orders         = pd.read_csv(str(DATA_DIR / "orders.csv"), parse_dates=["rent_start_dt"])
orders["hour"] = orders["rent_start_dt"].dt.hour

# ── 步驟 1：供給 — 各小時「平均」可用車數 ────────────────────
h_supply = (
    available_cars
    .groupby("available_hour")["available_cars"]
    .mean()                          # 注意：用 mean，不是 sum
    .reset_index()
    .rename(columns={"available_hour": "hour", "available_cars": "平均可用車數"})
)

# ── 步驟 2：需求 — 各小時「總」借車次數 ─────────────────────
h_demand = orders.groupby("hour").size().reset_index(name="借車次數")

# ── 步驟 3：合併兩份資料 ──────────────────────────────────────
merged = h_supply.merge(h_demand, on="hour", how="outer").sort_values("hour")

col1, col2 = st.columns([1, 3])
with col1:
    st.dataframe(merged, use_container_width=True)

with col2:
    # ── 步驟 4：建立支援雙 Y 軸的畫布 ────────────────────────
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    # specs=[[{"secondary_y": True}]]：告訴 plotly 這張圖需要兩條 y 軸

    # ── 步驟 5：加入長條圖（供給，左 Y 軸）──────────────────
    fig.add_trace(
        go.Bar(
            x=merged["hour"],
            y=merged["平均可用車數"],
            name="平均可用車數",
            marker_color="rgba(52, 152, 219, 0.6)",   # 半透明藍
        ),
        secondary_y=False,   # ← 左側 y 軸
    )

    # ── 步驟 6：加入折線圖（需求，右 Y 軸）──────────────────
    fig.add_trace(
        go.Scatter(
            x=merged["hour"],
            y=merged["借車次數"],
            name="借車次數",
            line=dict(color="#e74c3c", width=2.5),
        ),
        secondary_y=True,    # ← 右側 y 軸
    )

    fig.update_layout(
        title="逐小時供需對比",
        hovermode="x unified",
        xaxis=dict(title="小時", tickmode="linear", dtick=2),
    )
    fig.update_yaxes(title_text="平均可用車數（藍）", secondary_y=False)
    fig.update_yaxes(title_text="借車次數（紅）",      secondary_y=True)

    st.plotly_chart(fig, use_container_width=True)

st.info("""
**觀察：供給與需求的高峰是否對齊？**
- 車子多的時候，借車的人也多嗎？還是相反？
- 如果供不應求（車少但訂單多），是哪個時段？

**改改看：**
- 把 `"rgba(52, 152, 219, 0.6)"` 的透明度 0.6 改成 0.2 或 1.0
- 把 `go.Bar` 換成 `go.Scatter`，長條變折線
""")
