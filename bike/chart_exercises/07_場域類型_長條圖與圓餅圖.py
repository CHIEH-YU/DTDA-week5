# ============================================================
# 練習 07 ── 場域類型分析（長條圖 + 圓餅圖並排）
# ============================================================
# 學習重點：
#   1. st.columns 左右並排兩張圖
#   2. 從真實站點表統計站點數（不是從訂單）
#   3. 用同一份資料畫兩種不同圖表，比較差異
#   4. 從站名關鍵字推導場域類型
# 執行：streamlit run 07_場域類型_長條圖與圓餅圖.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 07｜場域類型", layout="wide")
st.title("練習 07｜場域類型分析（長條圖 + 圓餅圖）")
st.caption("資料來源：orders_real.json（真實 YouBike 2.0 站點）+ orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# ── 從站名關鍵字推導場域類型 ──────────────────────────────────
# YouBike 站點名稱本身蘊含位置資訊，可以用關鍵字分類
BIZ_KEYWORDS = {
    "捷運站周邊": ["捷運", "MRT"],
    "大學校園":   ["大學", "學院", "學校"],
    "公園綠地":   ["公園", "植物園", "綠地"],
    "購物商圈":   ["商圈", "市場", "百貨"],
    "觀光景點":   ["景點", "觀光", "博物館"],
}

def derive_biz_type(name: str) -> str:
    for biz, keywords in BIZ_KEYWORDS.items():
        if any(kw in name for kw in keywords):
            return biz
    return "住宅社區"   # 預設分類

# ── 載入真實站點資料 ──────────────────────────────────────────
with open(str(DATA_DIR / "orders_real.json"), encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)
stations["場域類型"] = stations["sna"].apply(derive_biz_type)

# ── 資料 A：各場域類型有幾個站點（來自真實站點）─────────────
biz_stations = (
    stations
    .groupby("場域類型")
    .size()
    .reset_index(name="站點數")
)

# ── 資料 B：各場域類型有幾筆訂單（需先 merge）────────────────
orders = pd.read_csv(
    str(DATA_DIR / "orders.csv"),
    dtype={"depart_parking_lot_id": str},
)
orders_geo = orders.merge(
    stations[["sno", "場域類型"]],
    left_on="depart_parking_lot_id",
    right_on="sno",
    how="left",
)
biz_orders = (
    orders_geo
    .groupby("場域類型")
    .size()
    .reset_index(name="借車次數")
)

# ── 左右並排：長條圖（站點數）& 圓餅圖（目前可借車輛佔比）──
col1, col2 = st.columns(2)

with col1:
    st.subheader("各場域類型站點數")
    fig1 = px.bar(
        biz_stations,
        x="場域類型",
        y="站點數",
        title="站點數量分布（真實 YouBike 2.0）",
        color="場域類型",
    )
    fig1.update_layout(showlegend=False, xaxis_title="")
    fig1.update_xaxes(tickangle=30)
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("各場域類型借車佔比")
    fig2 = px.pie(
        biz_orders,
        values="借車次數",
        names="場域類型",
        title="訂單佔比",
        hole=0.4,
    )
    st.plotly_chart(fig2, use_container_width=True)

# ── 觀察重點提示 ──────────────────────────────────────────────
st.info("""
**觀察：站點數 vs 訂單佔比是否一致？**
- 站點數多的場域，訂單也一定多嗎？
- 哪個場域的「單站效率」最高（訂單/站點 比值）？

**改改看：**
- 把 `col1, col2 = st.columns(2)` 改成 `col1, col2 = st.columns([2, 1])` 調整寬度比例
- 在 BIZ_KEYWORDS 新增一個場域類型，觀察分類如何改變
""")
