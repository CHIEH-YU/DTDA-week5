# ============================================================
# 練習 12 ── App 瀏覽 → 借車轉換率（長條圖）
# ============================================================
# 學習重點：
#   1. merge 兩個 groupby 結果，計算衍生指標
#   2. .round(2) 控制小數位數
#   3. color_continuous_scale="RdYlGn" 視覺化高低轉換率
# 執行：streamlit run 12_瀏覽轉換率_長條圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 12｜轉換率", layout="wide")
st.title("練習 12｜各小時 App 瀏覽 → 借車轉換率")
st.caption("資料來源：map_browsing.csv + orders.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"
browsing = pd.read_csv(str(DATA_DIR / "map_browsing.csv"))
orders   = pd.read_csv(str(DATA_DIR / "orders.csv"), parse_dates=["rent_start_dt"])
orders["hour"] = orders["rent_start_dt"].dt.hour

# ── 步驟 1：各小時瀏覽總點擊數 ───────────────────────────────
h_browse = (
    browsing
    .groupby("click_hour")["num_click_times"]
    .sum()
    .reset_index()
    .rename(columns={"click_hour": "hour", "num_click_times": "瀏覽次數"})
)

# ── 步驟 2：各小時借車次數 ────────────────────────────────────
h_demand = orders.groupby("hour").size().reset_index(name="借車次數")

# ── 步驟 3：merge 兩份資料，計算轉換率 ───────────────────────
bto = h_browse.merge(h_demand, on="hour", how="inner")
# 轉換率 = 借車次數 / 瀏覽次數 × 100%
bto["轉換率(%)"] = (bto["借車次數"] / bto["瀏覽次數"] * 100).round(2)
# .round(2) → 保留兩位小數

st.subheader("計算過程")
st.dataframe(bto, use_container_width=True)
st.markdown("---")

# ── 步驟 4：畫長條圖，顏色反映轉換率高低 ─────────────────────
fig = px.bar(
    bto,
    x="hour",
    y="轉換率(%)",
    title="各小時 App 瀏覽 → 借車轉換率",
    color="轉換率(%)",
    color_continuous_scale="RdYlGn",   # 紅（低）→ 黃 → 綠（高）
)
fig.update_layout(
    xaxis=dict(title="小時", tickmode="linear", dtick=2),
    coloraxis_showscale=False,
)

st.plotly_chart(fig, use_container_width=True)

# ── 小結 ──────────────────────────────────────────────────────
best_hour  = bto.loc[bto["轉換率(%)"].idxmax(), "hour"]
worst_hour = bto.loc[bto["轉換率(%)"].idxmin(), "hour"]
st.metric("轉換率最高小時", f"{best_hour}:00",
          delta=f"{bto.loc[bto['轉換率(%)'].idxmax(), '轉換率(%)']:.1f}%")
st.metric("轉換率最低小時", f"{worst_hour}:00",
          delta=f"{bto.loc[bto['轉換率(%)'].idxmin(), '轉換率(%)']:.1f}%",
          delta_color="inverse")

st.info("""
**改改看：**
- `how="inner"` 改成 `"outer"`，看看 merge 結果差異
- 加一欄 `bto["每次瀏覽帶來借車"] = bto["借車次數"] / bto["瀏覽次數"]`
- `color_continuous_scale="RdYlGn"` 改成 `"Blues"` 觀察視覺效果
""")
