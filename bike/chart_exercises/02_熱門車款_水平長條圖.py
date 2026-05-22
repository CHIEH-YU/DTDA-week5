# ============================================================
# 練習 02 ── 熱門車款 Top 10（水平長條圖）
# ============================================================
# 學習重點：
#   1. value_counts() 快速統計類別頻率
#   2. .head(N) 取前 N 名
#   3. orientation="h" 讓長條圖變水平
# 執行：streamlit run 02_熱門車款_水平長條圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 02｜熱門車款", layout="wide")
st.title("練習 02｜熱門車款 Top 10（水平長條圖）")
st.caption("資料來源：orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
orders = pd.read_csv(str(DATA_DIR / "orders.csv"))

# ── 步驟 1：統計每種車款出現幾次 ─────────────────────────────
bike_counts = orders["car_series_name"].value_counts()
# value_counts()：計算每個類別值出現幾次，並由多到少排序

# ── 步驟 2：只取前 10 名，轉成 DataFrame ─────────────────────
top10 = bike_counts.head(10).reset_index()
top10.columns = ["車款", "借車次數"]   # 重新命名欄位

st.dataframe(top10, use_container_width=True)
st.markdown("---")

# ── 步驟 3：畫水平長條圖 ──────────────────────────────────────
fig = px.bar(
    top10,
    x="借車次數",   # ← 數值放 x（水平方向）
    y="車款",       # ← 類別放 y（垂直排列）
    orientation="h",                    # "h" = horizontal 水平
    title="熱門車款 Top 10",
    color="借車次數",
    color_continuous_scale="Viridis",
)
fig.update_layout(
    coloraxis_showscale=False,
    yaxis_title="",   # y 軸標題留空，讓車款名稱自己說話
)

st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `.head(10)` 改成 `.head(5)` 只看前 5 名
- 把 `color_continuous_scale` 換成 "Oranges"
- 拿掉 `orientation="h"`，看看恢復成垂直長條圖
""")
