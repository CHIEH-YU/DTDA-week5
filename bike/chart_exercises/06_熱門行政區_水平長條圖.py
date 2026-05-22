# ============================================================
# 練習 06 ── 熱門行政區 Top 15（水平長條圖）
# ============================================================
# 學習重點：
#   1. merge：訂單表連接真實站點表取得行政區資訊
#   2. sort_values + head 篩選 Top N
#   3. orientation="h" 水平長條圖適合長標籤
# 執行：streamlit run 06_熱門行政區_水平長條圖.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 06｜熱門行政區", layout="wide")
st.title("練習 06｜熱門行政區 Top 15（水平長條圖）")
st.caption("資料來源：orders.csv + orders_real.json（真實 YouBike 2.0 站點）")

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# ── 載入真實站點資料 ──────────────────────────────────────────
with open(DATA_DIR / "orders_real.json", encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)

orders = pd.read_csv(
    DATA_DIR / "orders.csv",
    dtype={"depart_parking_lot_id": str},
)

# ── 步驟 1：合併行政區資訊 ────────────────────────────────────
orders_geo = orders.merge(
    stations[["sno", "sarea"]],
    left_on="depart_parking_lot_id",
    right_on="sno",
    how="left",
)

# ── 步驟 2：依行政區統計借車次數，取前 15 名 ─────────────────
area_counts = (
    orders_geo
    .groupby("sarea")          # 依行政區分組
    .size()
    .reset_index(name="借車次數")
    .sort_values("借車次數", ascending=False)   # 由多到少排序
    .head(15)                                   # 只取前 15 名
)

st.dataframe(area_counts, use_container_width=True)
st.markdown("---")

# ── 步驟 3：畫水平長條圖 ──────────────────────────────────────
fig = px.bar(
    area_counts,
    x="借車次數",
    y="sarea",
    orientation="h",
    title="熱門行政區 Top 15",
    color="借車次數",
    color_continuous_scale="Blues",
)
fig.update_layout(
    coloraxis_showscale=False,
    yaxis_title="",
    height=500,
)

st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `.head(15)` 改成 `.head(10)` 或 `.head(20)`
- `ascending=False` 改成 `True` 看從少到多排序
- `color_continuous_scale` 換成 "Oranges" 或 "Viridis"
- 把 `orientation="h"` 拿掉，改回垂直長條圖，比較哪種更好讀
""")
