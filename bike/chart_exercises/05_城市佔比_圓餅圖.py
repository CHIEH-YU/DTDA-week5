# ============================================================
# 練習 05 ── 行政區借車佔比（圓餅圖 / 甜甜圈圖 Donut Pie）
# ============================================================
# 學習重點：
#   1. merge：把訂單表與真實站點表連接，補上行政區資訊
#   2. px.pie 圓餅圖，hole=0.4 變甜甜圈
#   3. 從 JSON 讀取真實 YouBike 站點資料
# 執行：streamlit run 05_城市佔比_圓餅圖.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 05｜行政區佔比", layout="wide")
st.title("練習 05｜行政區借車佔比（甜甜圈圖）")
st.caption("資料來源：orders.csv + orders_real.json（真實 YouBike 2.0 站點）")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# ── 載入真實站點資料（JSON 格式）────────────────────────────
with open(str(DATA_DIR / "orders_real.json"), encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)   # 確保 ID 為字串

# ── 載入訂單（ID 欄位指定為字串，對齊站點 ID 格式）─────────
orders = pd.read_csv(
    str(DATA_DIR / "orders.csv"),
    dtype={"depart_parking_lot_id": str},
)

# ── 步驟 1：把訂單表與站點表合併，取得行政區欄位 ─────────────
# orders 只有 depart_parking_lot_id，要從 stations 拿行政區名稱
orders_geo = orders.merge(
    stations[["sno", "sarea"]],
    left_on="depart_parking_lot_id",   # 訂單表的站點 ID
    right_on="sno",                    # 站點表的站點 ID
    how="left",                        # left join：保留所有訂單
)
# 合併後 sarea 就是行政區欄位（如「大安區」、「中山區」）

# ── 步驟 2：按行政區統計借車次數 ─────────────────────────────
area_counts = (
    orders_geo
    .groupby("sarea")
    .size()
    .reset_index(name="借車次數")
    .sort_values("借車次數", ascending=False)
)

col1, col2 = st.columns([1, 2])
with col1:
    st.dataframe(area_counts, use_container_width=True)

with col2:
    # ── 步驟 3：畫甜甜圈圖 ────────────────────────────────────
    fig = px.pie(
        area_counts,
        values="借車次數",   # 決定每塊大小的欄位
        names="sarea",       # 每塊的標籤（行政區）
        title="各行政區借車次數佔比",
        hole=0.4,            # 0 = 實心圓餅；0.4 = 甜甜圈
    )
    st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `hole=0.4` 改成 `hole=0` 看看實心圓餅圖
- `hole=0.7` 讓洞更大
- 加上 `color_discrete_sequence=px.colors.qualitative.Set2` 換配色
- 在 groupby 後加 `.head(5)`，只顯示前 5 個行政區，其他合為「其他」
""")
