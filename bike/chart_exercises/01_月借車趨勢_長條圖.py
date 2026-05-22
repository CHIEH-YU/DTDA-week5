# ============================================================
# 練習 01 ── 月借車趨勢（長條圖 Bar Chart）
# ============================================================
# 學習重點：
#   1. 用 dt.to_period("M") 把日期轉成「年-月」字串
#   2. groupby + size() 統計每月筆數
#   3. px.bar 基本長條圖 + 色彩漸層
# 執行：streamlit run 01_月借車趨勢_長條圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 01｜月借車趨勢", layout="wide")
st.title("練習 01｜月借車趨勢（長條圖）")
st.caption("資料來源：orders.csv")

# ── 步驟 1：載入訂單資料，並解析日期欄位 ──────────────────────
DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
orders = pd.read_csv(
    str(DATA_DIR / "orders.csv"),
    parse_dates=["rent_start_dt"],   # 把這欄直接解析成 datetime
)

# ── 步驟 2：從 rent_start_dt 抽出「年-月」字串 ─────────────────
orders["month"] = orders["rent_start_dt"].dt.to_period("M").astype(str)
# .to_period("M")：把 2024-03-15 → Period('2024-03', 'M')
# .astype(str)   ：轉成字串 "2024-03"（畫圖用）

# ── 步驟 3：按月份統計借車次數 ────────────────────────────────
monthly = orders.groupby("month").size().reset_index(name="借車次數")
# groupby("month")：依月份分組
# .size()        ：計算每組有幾列（＝幾筆訂單）
# reset_index    ：把 index 變回普通欄位
# name="借車次數" ：幫計數欄命名

st.dataframe(monthly, use_container_width=True)  # 先看看資料長什麼樣
st.markdown("---")

# ── 步驟 4：畫長條圖 ──────────────────────────────────────────
fig = px.bar(
    monthly,
    x="month",           # x 軸：月份
    y="借車次數",         # y 軸：筆數
    title="月借車趨勢",
    color="借車次數",     # 依 y 值上色
    color_continuous_scale="Blues",  # 藍色漸層
)
fig.update_layout(
    coloraxis_showscale=False,  # 隱藏右側色條
    xaxis_title="月份",
)
fig.update_xaxes(tickangle=45)  # x 軸標籤斜 45 度，避免重疊

st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `color_continuous_scale` 換成 "Reds" 或 "Viridis" 看看變化
- 把 `color="借車次數"` 拿掉，長條圖會變成什麼樣？
- 把 `x` 和 `y` 互換，變成水平長條圖試試
""")
