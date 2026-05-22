# ============================================================
# 練習 09 ── App 瀏覽熱力圖（星期 × 小時）
# ============================================================
# 學習重點：
#   1. 承接練習 08，但資料來源換成 map_browsing.csv
#   2. groupby + sum()（加總點擊數）vs size()（計算列數）的差異
#   3. st.columns 並排比較兩張熱力圖
# 執行：streamlit run 09_App瀏覽熱力圖_星期x小時.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 09｜App 瀏覽熱力圖", layout="wide")
st.title("練習 09｜App 瀏覽熱力圖（星期 × 小時）")
st.caption("資料來源：map_browsing.csv")

DOW_MAP = {0: "週一", 1: "週二", 2: "週三", 3: "週四",
           4: "週五", 5: "週六", 6: "週日"}

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
browsing = pd.read_csv(DATA_DIR / "map_browsing.csv", parse_dates=["click_date"])
browsing["dow"] = browsing["click_date"].dt.dayofweek

# ── 步驟 1：雙維度分組，「加總」點擊次數 ─────────────────────
# ⚠️ 注意：這裡用 .sum()，不是 .size()
#   .size()  → 統計「有幾列記錄」
#   .sum()   → 把欄位數值加起來（這裡是 num_click_times）
mb_hm = (
    browsing
    .groupby(["dow", "click_hour"])["num_click_times"]
    .sum()
    .reset_index()
)

# ── 步驟 2：pivot 成矩陣 ──────────────────────────────────────
pivot = mb_hm.pivot(
    index="dow",
    columns="click_hour",
    values="num_click_times",
).fillna(0)
pivot.index = [DOW_MAP.get(i, i) for i in pivot.index]

# ── 步驟 3：畫熱力圖 ──────────────────────────────────────────
fig = px.imshow(
    pivot,
    labels=dict(x="小時", y="星期", color="點擊數"),
    title="App 瀏覽熱力圖（星期 × 小時）",
    color_continuous_scale="Blues",   # 藍色系，與訂單熱力圖區別
    aspect="auto",
)
st.plotly_chart(fig, use_container_width=True)

# ── 延伸：與訂單熱力圖並排比較 ───────────────────────────────
st.markdown("---")
st.subheader("🔍 延伸練習：和訂單熱力圖並排比較")

orders = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["rent_start_dt"])
orders["hour"] = orders["rent_start_dt"].dt.hour
orders["dow"]  = orders["rent_start_dt"].dt.dayofweek
ord_hm = orders.groupby(["dow", "hour"]).size().reset_index(name="借車次數")
ord_pivot = ord_hm.pivot(index="dow", columns="hour", values="借車次數").fillna(0)
ord_pivot.index = [DOW_MAP[i] for i in ord_pivot.index]

col1, col2 = st.columns(2)
with col1:
    fig1 = px.imshow(ord_pivot, title="訂單熱力圖",
                     color_continuous_scale="YlOrRd", aspect="auto")
    st.plotly_chart(fig1, use_container_width=True)
with col2:
    st.plotly_chart(fig, use_container_width=True)

st.info("""
**思考：瀏覽熱力圖 vs 訂單熱力圖的高峰是否一致？**
- 用戶在同一個時段瀏覽 App，也會在同一時段借車嗎？
- 這個「延遲」可以幫助我們推算預測模型的 lag 值
""")
