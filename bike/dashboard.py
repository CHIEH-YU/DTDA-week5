import pathlib
import warnings

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="台灣共享單車營運分析儀表板",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = pathlib.Path(__file__).parent / "data"
DOW_MAP = {0: "週一", 1: "週二", 2: "週三", 3: "週四", 4: "週五", 5: "週六", 6: "週日"}

_BIZ_KEYWORDS = {
    "捷運站周邊": ["捷運", "MRT"],
    "大學校園":   ["大學", "學院", "學校", "University", "College"],
    "公園綠地":   ["公園", "植物園", "綠地", "Park"],
    "購物商圈":   ["商圈", "市場", "百貨", "Mall", "Market"],
    "觀光景點":   ["景點", "觀光", "博物館", "Museum"],
}

def _derive_biz_type(name_series: "pd.Series") -> "pd.Series":
    result = ["住宅社區"] * len(name_series)
    for biz, keywords in _BIZ_KEYWORDS.items():
        mask = name_series.str.contains("|".join(keywords), na=False)
        for i, hit in enumerate(mask):
            if hit and result[i] == "住宅社區":
                result[i] = biz
    return result


# ── Data loading ──────────────────────────────────────────────────────────────

@st.cache_data
def load_orders() -> pd.DataFrame:
    df = pd.read_csv(
        DATA_DIR / "orders.csv",
        parse_dates=["booking_dt", "rent_start_dt", "rent_end_dt"],
        dtype={"depart_parking_lot_id": str, "return_parking_lot_id": str},
    )
    df["duration_min"] = (df["rent_end_dt"] - df["rent_start_dt"]).dt.total_seconds() / 60
    df["hour"] = df["rent_start_dt"].dt.hour
    df["dow"] = df["rent_start_dt"].dt.dayofweek
    df["date"] = df["rent_start_dt"].dt.normalize()
    df["month"] = df["rent_start_dt"].dt.to_period("M").astype(str)
    df["is_round_trip"] = df["depart_parking_lot_id"] == df["return_parking_lot_id"]
    return df


@st.cache_data
def load_real_stations() -> pd.DataFrame:
    """Real YouBike 2.0 station data from data.taipei (orders_real.json)."""
    import json as _json
    with open(DATA_DIR / "orders_real.json", encoding="utf-8") as f:
        raw = pd.DataFrame(_json.load(f))
    df = pd.DataFrame({
        "parking_lot_id":            raw["sno"].astype(str),
        "parking_lot_name":          raw["sna"].str.replace("YouBike2.0_", "", regex=False),
        "parking_lot_city":          "台北市",
        "parking_lot_area":          raw["sarea"],
        "parking_lot_longitude":     raw["longitude"],
        "parking_lot_latitude":      raw["latitude"],
        "parking_lot_biz_type_desc": _derive_biz_type(raw["sna"]),
        "min_rent_start_date":       raw["infoDate"],
        "max_rent_start_date":       raw["infoDate"],
        "available_rent_bikes":      raw["available_rent_bikes"],
        "available_return_bikes":    raw["available_return_bikes"],
        "total_slots":               raw["Quantity"].astype(int),
        "address":                   raw["ar"],
        "is_active":                 raw["act"].astype(str) == "1",
    })
    return df[df["is_active"]].reset_index(drop=True)


@st.cache_data
def load_available_cars() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "available_cars.csv", parse_dates=["available_date"])
    df["dow"] = df["available_date"].dt.dayofweek
    return df


@st.cache_data
def load_map_browsing() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "map_browsing.csv", parse_dates=["click_date"])
    df["dow"] = df["click_date"].dt.dayofweek
    return df


with st.spinner("載入資料中…"):
    orders = load_orders()
    real_stations = load_real_stations()
    available_cars = load_available_cars()
    map_browsing = load_map_browsing()

lot_cols = [
    "parking_lot_id", "parking_lot_name", "parking_lot_city",
    "parking_lot_area", "parking_lot_longitude", "parking_lot_latitude",
    "parking_lot_biz_type_desc",
]
orders_geo = orders.merge(
    real_stations[lot_cols],
    left_on="depart_parking_lot_id",
    right_on="parking_lot_id",
    how="left",
)


# ── Sidebar ───────────────────────────────────────────────────────────────────

st.sidebar.title("🚲 共享單車分析平台")
st.sidebar.markdown("---")

areas = ["全部"] + sorted(orders_geo["parking_lot_area"].dropna().unique())
selected_area = st.sidebar.selectbox("行政區篩選", areas)

biz_types = ["全部"] + sorted(real_stations["parking_lot_biz_type_desc"].dropna().unique())
selected_biz = st.sidebar.selectbox("場域類型篩選", biz_types)

min_d = orders_geo["date"].min().date()
max_d = orders_geo["date"].max().date()
date_range = st.sidebar.date_input("日期範圍", value=(min_d, max_d), min_value=min_d, max_value=max_d)

mask = pd.Series(True, index=orders_geo.index)
if selected_area != "全部":
    mask &= orders_geo["parking_lot_area"] == selected_area
if selected_biz != "全部":
    mask &= orders_geo["parking_lot_biz_type_desc"] == selected_biz
if len(date_range) == 2:
    mask &= (orders_geo["date"].dt.date >= date_range[0]) & (orders_geo["date"].dt.date <= date_range[1])

fo = orders_geo[mask].copy()

st.sidebar.markdown("---")
st.sidebar.metric("篩選後借車次數", f"{len(fo):,}")
st.sidebar.metric("篩選後用戶數", f"{fo['acct_id'].nunique():,}")
st.sidebar.caption(f"資料期間：{min_d} ～ {max_d}")


# ── Main ──────────────────────────────────────────────────────────────────────

st.title("🚲 台灣共享單車 營運分析儀表板")

tab1, tab2, tab3, tab4 = st.tabs(["📊 總覽", "🗺️ 地理分布", "📈 需求分析", "🔍 站點深探"])


# ════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ════════════════════════════════════════════════════════════
with tab1:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("總借車次數", f"{len(fo):,}")
    c2.metric("不重複用戶", f"{fo['acct_id'].nunique():,}")
    c3.metric("中位租借時長", f"{fo['duration_min'].median():.0f} 分鐘")
    c4.metric("中位騎乘里程", f"{fo['mileage_diff'].median():.1f} 公里")
    c5.metric("原站歸還比例", f"{fo['is_round_trip'].mean() * 100:.1f}%")

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        monthly = fo.groupby("month").size().reset_index(name="借車次數")
        fig = px.bar(
            monthly, x="month", y="借車次數", title="月借車趨勢",
            color="借車次數", color_continuous_scale="Blues",
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_title="月份")
        fig.update_xaxes(tickangle=45)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        bikes = fo["car_series_name"].value_counts().head(10).reset_index()
        bikes.columns = ["車款", "借車次數"]
        fig = px.bar(
            bikes, x="借車次數", y="車款", orientation="h",
            title="熱門車款 Top 10", color="借車次數", color_continuous_scale="Viridis",
        )
        fig.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        hourly = fo.groupby("hour").size().reset_index(name="借車次數")
        fig = px.area(
            hourly, x="hour", y="借車次數", title="24 小時借車分布",
            color_discrete_sequence=["#667eea"],
        )
        fig.update_layout(xaxis=dict(title="小時", tickmode="linear", dtick=2))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        dow_df = fo.groupby("dow").size().reset_index(name="借車次數")
        dow_df["星期"] = dow_df["dow"].map(DOW_MAP)
        fig = px.bar(
            dow_df, x="星期", y="借車次數", title="星期別借車分布",
            color="借車次數", color_continuous_scale="RdYlGn",
        )
        fig.update_layout(coloraxis_showscale=False, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 2 — GEOGRAPHIC DISTRIBUTION
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("站點地理分布")
    st.caption(f"地圖資料來源：台北市 YouBike 2.0 即時站點（{len(real_stations):,} 站）｜訂單分析使用模擬資料")

    mc1, mc2 = st.columns([2, 1])
    with mc1:
        map_color = st.radio("顏色依據", ["行政區", "場域類型", "可借車輛數"], horizontal=True)
    with mc2:
        min_slots = st.slider("最低停車格數篩選", 0, 60, 0, 5)

    sg = real_stations[real_stations["total_slots"] >= min_slots].copy()

    color_col = {
        "行政區":    "parking_lot_area",
        "場域類型":  "parking_lot_biz_type_desc",
        "可借車輛數": "available_rent_bikes",
    }[map_color]

    fig_map = px.scatter_mapbox(
        sg,
        lat="parking_lot_latitude",
        lon="parking_lot_longitude",
        color=color_col,
        size="available_rent_bikes" if map_color == "可借車輛數" else None,
        size_max=20,
        hover_name="parking_lot_name",
        hover_data={
            "parking_lot_area":           True,
            "parking_lot_biz_type_desc":  True,
            "available_rent_bikes":        True,
            "available_return_bikes":      True,
            "total_slots":                 True,
            "address":                     True,
            "parking_lot_longitude":       False,
            "parking_lot_latitude":        False,
            "is_active":                   False,
        },
        mapbox_style="open-street-map",
        zoom=11,
        center={"lat": 25.065, "lon": 121.542},
        height=580,
        color_continuous_scale="YlOrRd",
        title="YouBike 2.0 台北市即時站點分布",
    )
    fig_map.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
    st.plotly_chart(fig_map, use_container_width=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        area_pie = fo.groupby("parking_lot_area").size().reset_index(name="借車次數")
        fig = px.pie(area_pie, values="借車次數", names="parking_lot_area", title="各行政區借車次數佔比", hole=0.4)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        area_bar = (
            fo.groupby("parking_lot_area")
            .size()
            .reset_index(name="借車次數")
            .sort_values("借車次數", ascending=False)
            .head(15)
        )
        fig = px.bar(
            area_bar, x="借車次數", y="parking_lot_area", orientation="h",
            title="熱門行政區 Top 15", color="借車次數", color_continuous_scale="Blues",
        )
        fig.update_layout(coloraxis_showscale=False, yaxis_title="", height=450)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("場域類型分析（真實站點）")
    col1, col2 = st.columns(2)

    with col1:
        biz_lots = real_stations.groupby("parking_lot_biz_type_desc").size().reset_index(name="站點數")
        fig = px.bar(
            biz_lots, x="parking_lot_biz_type_desc", y="站點數",
            title="各場域類型站點數（YouBike 2.0）", color="parking_lot_biz_type_desc",
        )
        fig.update_layout(showlegend=False, xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        biz_avail = (
            real_stations.groupby("parking_lot_biz_type_desc")["available_rent_bikes"]
            .sum()
            .reset_index(name="可借車輛總數")
        )
        fig = px.pie(
            biz_avail, values="可借車輛總數", names="parking_lot_biz_type_desc",
            title="各場域類型目前可借車輛佔比", hole=0.4,
        )
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 3 — DEMAND ANALYSIS
# ════════════════════════════════════════════════════════════
with tab3:
    st.subheader("需求熱力圖")
    col1, col2 = st.columns(2)

    with col1:
        hm = fo.groupby(["dow", "hour"]).size().reset_index(name="借車次數")
        pivot = hm.pivot(index="dow", columns="hour", values="借車次數").fillna(0)
        pivot.index = [DOW_MAP[i] for i in pivot.index]
        fig = px.imshow(
            pivot,
            labels=dict(x="小時", y="星期", color="借車次數"),
            title="借車熱力圖（星期 × 小時）",
            color_continuous_scale="YlOrRd",
            aspect="auto",
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        mb_hm = map_browsing.groupby(["dow", "click_hour"])["num_click_times"].sum().reset_index()
        mb_pivot = mb_hm.pivot(index="dow", columns="click_hour", values="num_click_times").fillna(0)
        mb_pivot.index = [DOW_MAP.get(i, i) for i in mb_pivot.index]
        fig = px.imshow(
            mb_pivot,
            labels=dict(x="小時", y="星期", color="點擊數"),
            title="App 瀏覽熱力圖（星期 × 小時）",
            color_continuous_scale="Blues",
            aspect="auto",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("每日供需趨勢")

    daily_supply = (
        available_cars.groupby("available_date")["available_cars"]
        .sum()
        .reset_index()
        .rename(columns={"available_date": "date", "available_cars": "可用車輛總和"})
    )
    daily_orders = fo.groupby("date").size().reset_index(name="借車次數")
    daily_browse = (
        map_browsing.groupby("click_date")["num_click_times"]
        .sum()
        .reset_index()
        .rename(columns={"click_date": "date", "num_click_times": "瀏覽次數"})
    )
    daily = (
        daily_supply.merge(daily_orders, on="date", how="outer")
        .merge(daily_browse, on="date", how="outer")
        .sort_values("date")
    )
    daily = daily[(daily["date"] >= "2023-01-01") & (daily["date"] <= "2025-06-01")]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["借車次數"].rolling(7).mean(),
            name="借車次數（7日均）",
            line=dict(color="#e74c3c", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=daily["date"],
            y=daily["瀏覽次數"].rolling(7).mean(),
            name="App 瀏覽（7日均）",
            line=dict(color="#3498db", width=2, dash="dot"),
            yaxis="y2",
        )
    )
    fig.update_layout(
        title="每日借車次數 vs App 瀏覽次數（7日滾動平均）",
        yaxis=dict(title="借車次數", color="#e74c3c"),
        yaxis2=dict(title="App 瀏覽次數", color="#3498db", overlaying="y", side="right"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("逐小時供需分析")
    col1, col2 = st.columns(2)

    with col1:
        h_supply = (
            available_cars.groupby("available_hour")["available_cars"]
            .mean()
            .reset_index()
            .rename(columns={"available_hour": "hour", "available_cars": "平均可用車數"})
        )
        h_demand = fo.groupby("hour").size().reset_index(name="借車次數")
        merged_h = h_supply.merge(h_demand, on="hour", how="outer").sort_values("hour")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=merged_h["hour"], y=merged_h["平均可用車數"], name="平均可用車數",
                   marker_color="rgba(52,152,219,0.6)"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=merged_h["hour"], y=merged_h["借車次數"], name="借車次數",
                       line=dict(color="#e74c3c", width=2.5)),
            secondary_y=True,
        )
        fig.update_layout(
            title="逐小時供需對比",
            hovermode="x unified",
            xaxis=dict(title="小時", tickmode="linear", dtick=2),
        )
        fig.update_yaxes(title_text="平均可用車數", secondary_y=False)
        fig.update_yaxes(title_text="借車次數", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        h_browse = (
            map_browsing.groupby("click_hour")["num_click_times"]
            .sum()
            .reset_index()
            .rename(columns={"click_hour": "hour", "num_click_times": "瀏覽次數"})
        )
        bto = h_browse.merge(h_demand, on="hour", how="inner")
        bto["轉換率(%)"] = (bto["借車次數"] / bto["瀏覽次數"] * 100).round(2)

        fig = px.bar(
            bto, x="hour", y="轉換率(%)",
            title="各小時 App 瀏覽 → 借車轉換率",
            color="轉換率(%)", color_continuous_scale="RdYlGn",
        )
        fig.update_layout(
            xaxis=dict(title="小時", tickmode="linear", dtick=2),
            coloraxis_showscale=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("租借時長 & 里程分布")
    col1, col2 = st.columns(2)

    with col1:
        fig = px.histogram(
            fo[fo["duration_min"].between(0, 300)], x="duration_min", nbins=60,
            title="租借時長分布（分鐘）", color_discrete_sequence=["#667eea"],
        )
        fig.update_layout(xaxis_title="分鐘", yaxis_title="借車次數")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(
            fo[fo["mileage_diff"].between(0, 30)], x="mileage_diff", nbins=60,
            title="騎乘里程分布（公里）", color_discrete_sequence=["#e74c3c"],
        )
        fig.update_layout(xaxis_title="公里", yaxis_title="借車次數")
        st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════
# TAB 4 — STATION DEEP DIVE
# ════════════════════════════════════════════════════════════
with tab4:
    st.subheader("站點深入分析")

    top_n = (
        fo.groupby("depart_parking_lot_id")
        .size()
        .reset_index(name="借車次數")
        .merge(
            real_stations[["parking_lot_id", "parking_lot_name"]],
            left_on="depart_parking_lot_id",
            right_on="parking_lot_id",
            how="left",
        )
        .sort_values("借車次數", ascending=False)
    )
    top_n["label"] = (
        top_n["parking_lot_name"].fillna(top_n["parking_lot_id"].astype(str))
        + " ("
        + top_n["借車次數"].astype(str)
        + " 筆)"
    )

    sel_id = st.selectbox(
        "選擇站點（依借車次數排序，前 50）",
        options=top_n["parking_lot_id"].head(50).tolist(),
        format_func=lambda x: (
            top_n.loc[top_n["parking_lot_id"] == x, "label"].values[0]
            if (top_n["parking_lot_id"] == x).any()
            else str(x)
        ),
    )

    sinfo_df = real_stations[real_stations["parking_lot_id"] == sel_id]
    if not sinfo_df.empty:
        sinfo = sinfo_df.iloc[0]
        st.markdown(f"### 📍 {sinfo['parking_lot_name']}")
        ci1, ci2, ci3, ci4 = st.columns(4)
        ci1.info(f"**行政區**: {sinfo['parking_lot_area']}")
        ci2.info(f"**場域類型**: {sinfo['parking_lot_biz_type_desc']}")
        ci3.info(f"**總停車格**: {sinfo['total_slots']} 格")
        ci4.info(f"**目前可借**: {sinfo['available_rent_bikes']} 輛 ／ 空位 {sinfo['available_return_bikes']} 格")

    s_ord   = fo[fo["depart_parking_lot_id"] == sel_id].copy()
    s_avail = available_cars[available_cars["parking_lot_id"] == sel_id]
    s_browse = map_browsing[map_browsing["parking_lot_id"] == sel_id]

    st.markdown(f"共 **{len(s_ord):,}** 筆借車 · **{s_ord['acct_id'].nunique():,}** 名用戶")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        sh = s_ord.groupby("hour").size().reset_index(name="借車次數")
        fig = px.bar(
            sh, x="hour", y="借車次數", title="每小時借車分布",
            color="借車次數", color_continuous_scale="YlOrRd",
        )
        fig.update_layout(xaxis=dict(title="小時", tickmode="linear", dtick=2), coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        sa_h = (
            s_avail.groupby("available_hour")["available_cars"]
            .mean()
            .reset_index()
            .rename(columns={"available_hour": "hour", "available_cars": "平均可用車數"})
        )
        merged_s = sa_h.merge(sh, on="hour", how="outer").sort_values("hour")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Bar(x=merged_s["hour"], y=merged_s["平均可用車數"], name="平均可用車數",
                   marker_color="rgba(52,152,219,0.6)"),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=merged_s["hour"], y=merged_s["借車次數"], name="借車次數",
                       line=dict(color="#e74c3c", width=2.5)),
            secondary_y=True,
        )
        fig.update_layout(
            title="站點供需對比（逐小時）",
            hovermode="x unified",
            xaxis=dict(title="小時", tickmode="linear", dtick=2),
        )
        fig.update_yaxes(title_text="平均可用車數", secondary_y=False)
        fig.update_yaxes(title_text="借車次數", secondary_y=True)
        st.plotly_chart(fig, use_container_width=True)

    if not s_browse.empty:
        sb_h = (
            s_browse.groupby("click_hour")["num_click_times"]
            .sum()
            .reset_index()
            .rename(columns={"click_hour": "hour", "num_click_times": "瀏覽次數"})
        )
        bto_s = sb_h.merge(sh, on="hour", how="outer").sort_values("hour")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(x=bto_s["hour"], y=bto_s["瀏覽次數"], name="App 瀏覽次數",
                   marker_color="rgba(52,152,219,0.5)")
        )
        fig.add_trace(
            go.Scatter(x=bto_s["hour"], y=bto_s["借車次數"], name="借車次數",
                       line=dict(color="#e74c3c", width=2.5), yaxis="y2")
        )
        fig.update_layout(
            title="站點 App 瀏覽 vs 實際借車次數",
            yaxis=dict(title="瀏覽次數"),
            yaxis2=dict(title="借車次數", overlaying="y", side="right"),
            hovermode="x unified",
            legend=dict(orientation="h"),
            xaxis=dict(title="小時", tickmode="linear", dtick=2),
        )
        st.plotly_chart(fig, use_container_width=True)

    s_monthly = s_ord.groupby("month").size().reset_index(name="借車次數")
    fig = px.area(s_monthly, x="month", y="借車次數", title="站點月借車趨勢",
                  color_discrete_sequence=["#667eea"])
    fig.update_xaxes(tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

    one_way = s_ord[~s_ord["is_round_trip"]]
    if len(one_way) > 0:
        st.markdown("---")
        st.subheader("常見還車站點（異站歸還）")
        dest = (
            one_way.groupby("return_parking_lot_id")
            .size()
            .reset_index(name="次數")
            .merge(real_stations[["parking_lot_id", "parking_lot_name"]],
                   left_on="return_parking_lot_id", right_on="parking_lot_id", how="left")
            .sort_values("次數", ascending=False)
            .head(10)
        )
        dest["還車站點"] = dest["parking_lot_name"].fillna(dest["return_parking_lot_id"].astype(str))
        fig = px.bar(
            dest, x="次數", y="還車站點", orientation="h",
            title="熱門還車站點 Top 10", color="次數", color_continuous_scale="Oranges",
        )
        fig.update_layout(coloraxis_showscale=False, yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)
