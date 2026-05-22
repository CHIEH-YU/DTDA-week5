# ============================================================
# 練習 04 ── 星期別借車分布（長條圖 + 中文標籤）
# ============================================================
# 學習重點：
#   1. dt.dayofweek 取得星期數（0=週一 … 6=週日）
#   2. .map(字典) 把數字對應成中文標籤
#   3. color_continuous_scale="RdYlGn" 紅黃綠漸層
# 執行：streamlit run 04_星期別分布_長條圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 04｜星期別分布", layout="wide")
st.title("練習 04｜星期別借車分布（長條圖）")
st.caption("資料來源：orders.csv")

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
orders = pd.read_csv(DATA_DIR / "orders.csv", parse_dates=["rent_start_dt"])

# ── 步驟 1：抽出星期數（0=週一, 6=週日）─────────────────────
orders["dow"] = orders["rent_start_dt"].dt.dayofweek

# ── 步驟 2：定義數字 → 中文星期的對照表 ─────────────────────
DOW_MAP = {0: "週一", 1: "週二", 2: "週三", 3: "週四",
           4: "週五", 5: "週六", 6: "週日"}

# ── 步驟 3：按星期分組統計，並加上中文標籤欄位 ────────────────
dow_df = orders.groupby("dow").size().reset_index(name="借車次數")
dow_df["星期"] = dow_df["dow"].map(DOW_MAP)
# .map(字典)：把 0 → "週一"、1 → "週二" …

st.dataframe(dow_df[["星期", "借車次數"]], use_container_width=True)
st.markdown("---")

# ── 步驟 4：畫長條圖 ──────────────────────────────────────────
fig = px.bar(
    dow_df,
    x="星期",       # 用中文標籤當 x 軸
    y="借車次數",
    title="星期別借車分布",
    color="借車次數",
    color_continuous_scale="RdYlGn",   # 紅（低）→ 黃 → 綠（高）
)
fig.update_layout(
    coloraxis_showscale=False,
    xaxis_title="",   # 不需要 x 軸標題（星期名稱已夠清楚）
)

st.plotly_chart(fig, use_container_width=True)

# ── 🔧 試試看 ──────────────────────────────────────────────────
st.info("""
**改改看：**
- `color_continuous_scale` 換成 "Blues" 觀察不同視覺效果
- 把 `x="星期"` 換回 `x="dow"`，標籤會變成什麼？
- 把 DOW_MAP 裡的值換成英文（"Mon", "Tue" …）
""")
