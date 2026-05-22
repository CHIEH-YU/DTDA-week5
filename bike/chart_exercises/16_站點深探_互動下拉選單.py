# ============================================================
# 練習 16 ── 站點深探（互動下拉選單 + 多圖）【綜合練習】
# ============================================================
# 學習重點：
#   1. st.selectbox 讓使用者選擇要分析的站點
#   2. 依選擇動態過濾資料，更新所有圖表
#   3. 綜合運用前面練習學過的所有圖表類型
#   4. 結合真實站點資訊（可借車數、空位數）
# 執行：streamlit run 16_站點深探_互動下拉選單.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

st.set_page_config(page_title="練習 16｜站點深探", layout="wide")
st.title("練習 16｜站點深探【綜合練習】")
st.caption("資料來源：orders.csv + orders_real.json + available_cars.csv")

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"

# ── 載入真實站點資料 ──────────────────────────────────────────
with open(DATA_DIR / "orders_real.json", encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)
stations["站名"] = stations["sna"].str.replace("YouBike2.0_", "", regex=False)
stations["Quantity"] = stations["Quantity"].astype(int)

# ── 載入訂單與供給資料 ────────────────────────────────────────
orders = pd.read_csv(
    DATA_DIR / "orders.csv",
    parse_dates=["rent_start_dt"],
    dtype={"depart_parking_lot_id": str, "return_parking_lot_id": str},
)
available_cars = pd.read_csv(DATA_DIR / "available_cars.csv")
available_cars["parking_lot_id"] = available_cars["parking_lot_id"].astype(str)

orders["hour"]  = orders["rent_start_dt"].dt.hour
orders["month"] = orders["rent_start_dt"].dt.to_period("M").astype(str)
orders["is_round_trip"] = (
    orders["depart_parking_lot_id"] == orders["return_parking_lot_id"]
)

# 合併行政區 & 站名到訂單
orders_geo = orders.merge(
    stations[["sno", "站名", "sarea"]],
    left_on="depart_parking_lot_id",
    right_on="sno",
    how="left",
)

# ── 步驟 1：建立下拉選單的選項清單（依借車次數排序）──────────
top_stations = (
    orders_geo
    .groupby("depart_parking_lot_id")
    .size()
    .reset_index(name="借車次數")
    .merge(stations[["sno", "站名"]], left_on="depart_parking_lot_id",
           right_on="sno", how="left")
    .sort_values("借車次數", ascending=False)
    .head(30)
)
top_stations["label"] = (
    top_stations["站名"].fillna("未知")
    + "（" + top_stations["借車次數"].astype(str) + " 筆）"
)

# ── 步驟 2：st.selectbox 讓使用者選站點 ──────────────────────
sel_label = st.selectbox(
    "選擇站點（依借車次數排序，前 30）",
    options=top_stations["label"].tolist(),
)
sel_id = top_stations.loc[
    top_stations["label"] == sel_label, "depart_parking_lot_id"
].values[0]

# ── 步驟 3：依選擇過濾資料 ───────────────────────────────────
s_ord   = orders_geo[orders_geo["depart_parking_lot_id"] == sel_id].copy()
s_avail = available_cars[available_cars["parking_lot_id"] == sel_id]

# 站點基本資訊（從真實資料取得）
sinfo = stations[stations["sno"] == sel_id]
if not sinfo.empty:
    sinfo = sinfo.iloc[0]
    st.markdown(f"### 📍 {sinfo['站名']}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("借車次數", f"{len(s_ord):,}")
    c2.metric("不重複用戶", f"{s_ord['acct_id'].nunique():,}")
    c3.metric("原站歸還率", f"{s_ord['is_round_trip'].mean() * 100:.1f}%")
    c4.info(f"**行政區**：{sinfo['sarea']}｜總格數 {sinfo['Quantity']} ｜可借 {sinfo['available_rent_bikes']} 輛")

st.markdown("---")

# ── 圖 1：每小時借車分布（長條圖）────────────────────────────
col1, col2 = st.columns(2)
with col1:
    sh = s_ord.groupby("hour").size().reset_index(name="借車次數")
    fig = px.bar(sh, x="hour", y="借車次數", title="每小時借車分布",
                 color="借車次數", color_continuous_scale="YlOrRd")
    fig.update_layout(xaxis=dict(title="小時", tickmode="linear", dtick=2),
                      coloraxis_showscale=False)
    st.plotly_chart(fig, use_container_width=True)

# ── 圖 2：供需對比（Bar + Line 複合圖）───────────────────────
with col2:
    sa_h = (
        s_avail.groupby("available_hour")["available_cars"]
        .mean().reset_index()
        .rename(columns={"available_hour": "hour", "available_cars": "平均可用車數"})
    )
    merged = sa_h.merge(sh, on="hour", how="outer").sort_values("hour")

    fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    fig2.add_trace(
        go.Bar(x=merged["hour"], y=merged["平均可用車數"],
               name="平均可用車數", marker_color="rgba(52,152,219,0.6)"),
        secondary_y=False,
    )
    fig2.add_trace(
        go.Scatter(x=merged["hour"], y=merged["借車次數"],
                   name="借車次數", line=dict(color="#e74c3c", width=2.5)),
        secondary_y=True,
    )
    fig2.update_layout(title="站點供需對比（逐小時）", hovermode="x unified",
                       xaxis=dict(title="小時", tickmode="linear", dtick=2))
    fig2.update_yaxes(title_text="平均可用車數", secondary_y=False)
    fig2.update_yaxes(title_text="借車次數",     secondary_y=True)
    st.plotly_chart(fig2, use_container_width=True)

# ── 圖 3：月借車趨勢（區域圖）────────────────────────────────
s_monthly = s_ord.groupby("month").size().reset_index(name="借車次數")
fig3 = px.area(s_monthly, x="month", y="借車次數", title="站點月借車趨勢",
               color_discrete_sequence=["#667eea"])
fig3.update_xaxes(tickangle=45)
st.plotly_chart(fig3, use_container_width=True)

# ── 圖 4：常見還車目的地（只有異站還車）──────────────────────
one_way = s_ord[~s_ord["is_round_trip"]]
if len(one_way) > 0:
    dest = (
        one_way.groupby("return_parking_lot_id").size()
        .reset_index(name="次數")
        .merge(stations[["sno", "站名"]],
               left_on="return_parking_lot_id", right_on="sno", how="left")
        .sort_values("次數", ascending=False).head(10)
    )
    dest["還車站點"] = dest["站名"].fillna(dest["return_parking_lot_id"].astype(str))
    fig4 = px.bar(dest, x="次數", y="還車站點", orientation="h",
                  title="熱門還車站點 Top 10", color="次數",
                  color_continuous_scale="Oranges")
    fig4.update_layout(coloraxis_showscale=False, yaxis_title="")
    st.plotly_chart(fig4, use_container_width=True)

st.info("""
**🎯 綜合練習重點：**
- st.selectbox → 動態過濾資料 → 更新圖表，這是 Streamlit 的核心互動模式
- 每次選擇改變，Streamlit 會從頭重跑整個腳本
- 真實站點資料讓我們能顯示「目前可借車數」這類即時資訊
- 思考：如果要加一個「行政區篩選」在 selectbox 前面，怎麼實作？
""")
