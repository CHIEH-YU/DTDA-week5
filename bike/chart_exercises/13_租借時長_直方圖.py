# ============================================================
# 練習 13 ── 租借時長分布（直方圖 Histogram）
# ============================================================
# 學習重點：
#   1. 兩個 datetime 相減，轉換成分鐘（duration）
#   2. .between(a, b) 過濾極端值
#   3. px.histogram 基本直方圖 + nbins 控制分組數
# 執行：streamlit run 13_租借時長_直方圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 13｜租借時長", layout="wide")
st.title("練習 13｜租借時長分布（直方圖）")
st.caption("資料來源：orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
orders = pd.read_csv(
    str(DATA_DIR / "orders.csv"),
    parse_dates=["rent_start_dt", "rent_end_dt"],
)

# ── 步驟 1：計算租借時長（分鐘）─────────────────────────────
orders["duration_min"] = (
    (orders["rent_end_dt"] - orders["rent_start_dt"])  # Timedelta 相減
    .dt.total_seconds()                                 # 轉成秒數
    / 60                                                # 秒 → 分鐘
)

st.write("基本統計：")
st.dataframe(orders["duration_min"].describe().round(1).to_frame().T,
             use_container_width=True)
st.markdown("---")

# ── 步驟 2：過濾極端值 ───────────────────────────────────────
# .between(0, 300)：只保留 0~300 分鐘的資料，排除異常值
filtered = orders[orders["duration_min"].between(0, 300)]
st.caption(f"過濾後資料筆數：{len(filtered):,}（原始：{len(orders):,}）")

# ── 步驟 3：畫直方圖 ──────────────────────────────────────────
nbins = st.slider("分組數（nbins）", min_value=10, max_value=120,
                  value=60, step=10)

fig = px.histogram(
    filtered,
    x="duration_min",
    nbins=nbins,              # 把 x 軸範圍切成幾段
    title="租借時長分布（分鐘）",
    color_discrete_sequence=["#667eea"],
)
fig.update_layout(
    xaxis_title="分鐘",
    yaxis_title="借車次數",
    bargap=0.05,   # 長條之間的間距
)
# 加上垂直中位線
median_val = filtered["duration_min"].median()
fig.add_vline(
    x=median_val,
    line_dash="dash",
    line_color="red",
    annotation_text=f"中位數 {median_val:.0f} 分",
)

st.plotly_chart(fig, use_container_width=True)

st.info("""
**改改看：**
- 拖動上方滑桿，調整 nbins 觀察分布粗細的變化
- `.between(0, 300)` 改成 `.between(0, 60)`，只看 1 小時內的資料
- `bargap=0.05` 改成 `0` 或 `0.3`，長條間距有什麼變化？
""")
