# ============================================================
# 練習 14 ── 騎乘里程分布（直方圖 + 分行政區疊加）
# ============================================================
# 學習重點：
#   1. 承接練習 13，直方圖的進階用法
#   2. color="sarea" 依行政區分組疊加直方圖
#   3. barmode="overlay" vs "stack" 的差異
# 執行：streamlit run 14_騎乘里程_直方圖.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 14｜騎乘里程", layout="wide")
st.title("練習 14｜騎乘里程分布（直方圖）")
st.caption("資料來源：orders.csv + orders_real.json（真實 YouBike 2.0 站點）")

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# ── 載入真實站點資料 ──────────────────────────────────────────
with open(DATA_DIR / "orders_real.json", encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)

orders = pd.read_csv(
    DATA_DIR / "orders.csv",
    dtype={"depart_parking_lot_id": str},
)
orders_geo = orders.merge(
    stations[["sno", "sarea"]],
    left_on="depart_parking_lot_id",
    right_on="sno",
    how="left",
)

# ── 過濾極端值 ────────────────────────────────────────────────
filtered = orders_geo[orders_geo["mileage_diff"].between(0, 30)]

st.write("基本統計：")
st.dataframe(filtered["mileage_diff"].describe().round(2).to_frame().T,
             use_container_width=True)
st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    # ── 基本直方圖（全部行政區合併）──────────────────────────
    fig1 = px.histogram(
        filtered,
        x="mileage_diff",
        nbins=60,
        title="騎乘里程分布（全部行政區）",
        color_discrete_sequence=["#e74c3c"],
    )
    fig1.update_layout(xaxis_title="公里", yaxis_title="借車次數")
    median_val = filtered["mileage_diff"].median()
    fig1.add_vline(x=median_val, line_dash="dash", line_color="navy",
                   annotation_text=f"中位數 {median_val:.1f} km")
    st.plotly_chart(fig1, use_container_width=True)

with col_right:
    # ── 進階：選行政區做疊加比較 ──────────────────────────────
    top_areas = (
        filtered["sarea"].value_counts().head(5).index.tolist()
    )
    selected_areas = st.multiselect(
        "選擇要比較的行政區（建議 2~4 個）",
        options=filtered["sarea"].dropna().unique().tolist(),
        default=top_areas[:3],
    )
    barmode = st.radio("疊加模式", ["overlay", "stack"], horizontal=True)

    subset = filtered[filtered["sarea"].isin(selected_areas)] if selected_areas else filtered
    fig2 = px.histogram(
        subset,
        x="mileage_diff",
        nbins=40,
        color="sarea",             # 每個行政區一個顏色
        title=f"各行政區里程分布（{barmode}）",
        barmode=barmode,
        # "overlay"：透明疊加，可以看出分布形狀差異
        # "stack"  ：堆疊，可以看出各行政區佔比
        opacity=0.7,
    )
    fig2.update_layout(xaxis_title="公里", yaxis_title="借車次數")
    st.plotly_chart(fig2, use_container_width=True)

st.info("""
**觀察：各行政區的里程分布有差異嗎？**
- 內湖區、士林區的騎乘距離通常比市中心長還是短？
- 切換 "overlay" / "stack" 觀察兩種模式適合什麼場合

**改改看：**
- `between(0, 30)` 改成 `between(0, 10)` 只看短途騎乘
- `nbins=40` 改成 `nbins=20`，分布形狀有何不同
""")
