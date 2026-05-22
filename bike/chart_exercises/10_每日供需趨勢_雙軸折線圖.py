# ============================================================
# 練習 10 ── 每日供需趨勢（雙 Y 軸折線圖）
# ============================================================
# 學習重點：
#   1. 三張表 merge（供給 + 需求 + 瀏覽）
#   2. 滾動平均 .rolling(7).mean() 平滑曲線
#   3. go.Figure + yaxis2 做雙 Y 軸（plotly.graph_objects）
# 執行：streamlit run 10_每日供需趨勢_雙軸折線圖.py
# ============================================================

import pathlib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="練習 10｜供需趨勢", layout="wide")
st.title("練習 10｜每日供需趨勢（雙 Y 軸折線圖）")
st.caption("資料來源：available_cars.csv + orders.csv + map_browsing.csv")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# ── 步驟 1：各自準備三個「每日匯總」資料 ─────────────────────
available_cars = pd.read_csv(str(DATA_DIR / "available_cars.csv"),
                             parse_dates=["available_date"])
orders         = pd.read_csv(str(DATA_DIR / "orders.csv"),
                             parse_dates=["rent_start_dt"])
map_browsing   = pd.read_csv(str(DATA_DIR / "map_browsing.csv"),
                             parse_dates=["click_date"])

orders["date"] = orders["rent_start_dt"].dt.normalize()  # 只留日期部分

daily_supply = (
    available_cars.groupby("available_date")["available_cars"]
    .sum().reset_index()
    .rename(columns={"available_date": "date", "available_cars": "可用車輛"})
)
daily_orders = orders.groupby("date").size().reset_index(name="借車次數")
daily_browse = (
    map_browsing.groupby("click_date")["num_click_times"]
    .sum().reset_index()
    .rename(columns={"click_date": "date", "num_click_times": "瀏覽次數"})
)

# ── 步驟 2：三表依日期 merge ──────────────────────────────────
daily = (
    daily_supply
    .merge(daily_orders, on="date", how="outer")
    .merge(daily_browse, on="date", how="outer")
    .sort_values("date")
)
# how="outer"：保留所有日期，即使某天某資料缺失也不丟棄

# ── 步驟 3：7 日滾動平均（平滑掉短期波動）────────────────────
daily["借車7日均"]  = daily["借車次數"].rolling(7).mean()
daily["瀏覽7日均"]  = daily["瀏覽次數"].rolling(7).mean()
# rolling(7)：以當列為中心取前 7 列的視窗
# .mean()   ：視窗內取平均

st.dataframe(daily.tail(10), use_container_width=True)
st.markdown("---")

# ── 步驟 4：go.Figure 雙 Y 軸折線圖 ──────────────────────────
# px 不支援雙 Y 軸，要用 graph_objects 手動設定
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=daily["date"],
    y=daily["借車7日均"],
    name="借車次數（7日均）",
    line=dict(color="#e74c3c", width=2),
    # yaxis 預設是 "y"（左側）
))

fig.add_trace(go.Scatter(
    x=daily["date"],
    y=daily["瀏覽7日均"],
    name="App 瀏覽（7日均）",
    line=dict(color="#3498db", width=2, dash="dot"),
    yaxis="y2",   # ← 指定用右側的第二條 y 軸
))

fig.update_layout(
    title="每日借車次數 vs App 瀏覽（7日滾動平均）",
    yaxis=dict(title="借車次數", color="#e74c3c"),
    yaxis2=dict(                           # 定義右側 y 軸
        title="App 瀏覽次數",
        color="#3498db",
        overlaying="y",   # 疊在左軸上
        side="right",     # 放右邊
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    hovermode="x unified",   # 懸停時同時顯示兩條線的值
)

st.plotly_chart(fig, use_container_width=True)

st.info("""
**改改看：**
- `rolling(7)` 改成 `rolling(14)` 或 `rolling(30)`，觀察曲線平滑程度
- `dash="dot"` 改成 `dash="dash"` 或拿掉，線型會變
- `hovermode="x unified"` 改成 `"closest"` 看看懸停效果差異
""")
