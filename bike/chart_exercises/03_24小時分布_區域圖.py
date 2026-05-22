# ============================================================
# 練習 03 ── 24 小時借車分布（區域圖 Area Chart）
# ============================================================
# 學習重點：
#   1. dt.hour 從 datetime 抽出「小時」欄位
#   2. px.area 區域圖（折線下方填色）
#   3. tickmode="linear", dtick=2 設定 x 軸刻度間距
# 執行：streamlit run 03_24小時分布_區域圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 03｜24小時分布", layout="wide")
st.title("練習 03｜24 小時借車分布（區域圖）")
st.caption("資料來源：orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
orders = pd.read_csv(str(DATA_DIR / "orders.csv"), parse_dates=["rent_start_dt"])

# ── 步驟 1：從 rent_start_dt 抽出「小時」欄位 ─────────────────
orders["hour"] = orders["rent_start_dt"].dt.hour
# dt.hour：取 datetime 的小時部分（0~23）

# ── 步驟 2：按小時統計借車次數 ────────────────────────────────
hourly = orders.groupby("hour").size().reset_index(name="借車次數")

st.dataframe(hourly.T, use_container_width=True)   # 橫向顯示方便對照
st.markdown("---")

# ── 步驟 3：畫區域圖 ──────────────────────────────────────────
fig = px.area(
    hourly,
    x="hour",
    y="借車次數",
    title="24 小時借車分布",
    color_discrete_sequence=["#667eea"],   # 指定單一顏色
    # px.area 會自動把折線下方填滿同色（較淡）
)
fig.update_layout(
    xaxis=dict(
        title="小時",
        tickmode="linear",   # 強制等距刻度
        dtick=2,             # 每 2 小時一個刻度
    )
)

st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- 把 `px.area` 換成 `px.line`，看看有什麼差別
- `color_discrete_sequence=["#e74c3c"]` 換成紅色試試
- `dtick=2` 改成 `dtick=1`，刻度密度會變怎樣？
""")
