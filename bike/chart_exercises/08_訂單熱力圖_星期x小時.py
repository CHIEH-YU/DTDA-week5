# ============================================================
# 練習 08 ── 訂單熱力圖（星期 × 小時）
# ============================================================
# 學習重點：
#   1. 雙維度 groupby（dow + hour）建立交叉統計
#   2. .pivot() 把長表轉成寬表（矩陣形式）
#   3. px.imshow 把 DataFrame 矩陣畫成熱力圖
# 執行：streamlit run 08_訂單熱力圖_星期x小時.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 08｜訂單熱力圖", layout="wide")
st.title("練習 08｜訂單熱力圖（星期 × 小時）")
st.caption("資料來源：orders.csv")

DOW_MAP = {0: "週一", 1: "週二", 2: "週三", 3: "週四",
           4: "週五", 5: "週六", 6: "週日"}

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
orders = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["rent_start_dt"])
orders["hour"] = orders["rent_start_dt"].dt.hour
orders["dow"]  = orders["rent_start_dt"].dt.dayofweek

# ── 步驟 1：雙維度分組統計 ─────────────────────────────────────
hm = orders.groupby(["dow", "hour"]).size().reset_index(name="借車次數")
# 結果是「長表」：每一列是一個 (星期, 小時) 組合

st.subheader("長表（pivot 前）")
st.dataframe(hm.head(10), use_container_width=True)
st.markdown("---")

# ── 步驟 2：pivot 長表 → 寬表（矩陣） ────────────────────────
pivot = hm.pivot(
    index="dow",      # 列 = 星期
    columns="hour",   # 欄 = 小時
    values="借車次數",
).fillna(0)           # 沒有資料的格子填 0
pivot.index = [DOW_MAP[i] for i in pivot.index]  # 把 0,1,... 換成中文

st.subheader("寬表（pivot 後，這就是熱力圖的資料）")
st.dataframe(pivot, use_container_width=True)
st.markdown("---")

# ── 步驟 3：px.imshow 畫熱力圖 ────────────────────────────────
fig = px.imshow(
    pivot,
    labels=dict(x="小時", y="星期", color="借車次數"),
    title="訂單熱力圖（星期 × 小時）",
    color_continuous_scale="YlOrRd",   # 黃→橘→紅（深=多）
    aspect="auto",                     # 自動調整格子比例
)
st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `color_continuous_scale` 換成 "Blues" 或 "Greens"
- 把 `index="dow"` 和 `columns="hour"` 互換，圖會轉 90 度
- 把 `.fillna(0)` 改成 `.fillna(-1)`，觀察空值如何顯示
""")
