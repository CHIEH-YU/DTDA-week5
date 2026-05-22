# ============================================================
# 練習 15 ── 站點地圖（散點地圖 Scatter Mapbox）
# ============================================================
# 學習重點：
#   1. 讀取真實 YouBike 2.0 站點（JSON 格式）
#   2. px.scatter_mapbox 地圖散點（需要 lat/lon）
#   3. size、color、hover_data 控制點的外觀和資訊
#   4. 用即時可借車數做視覺化
# 執行：streamlit run 15_站點地圖_散點地圖.py
# ============================================================

import json
import pathlib
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="練習 15｜站點地圖", layout="wide")
st.title("練習 15｜YouBike 2.0 站點地圖（散點地圖）")
st.caption("資料來源：orders_real.json（台北市 YouBike 2.0 即時站點）")

DATA_DIR = pathlib.Path(__file__).resolve().parent.parent / "data"

# ── 步驟 1：載入真實站點資料（JSON 格式）────────────────────
with open(str(DATA_DIR / "orders_real.json"), encoding="utf-8") as f:
    stations = pd.DataFrame(json.load(f))

# 只保留啟用中的站點（act == "1"）
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["sno"] = stations["sno"].astype(str)
# 清除站名前綴
stations["站名"] = stations["sna"].str.replace("YouBike2.0_", "", regex=False)
stations["Quantity"] = stations["Quantity"].astype(int)

st.metric("啟用站點數", f"{len(stations):,} 站")

# ── 步驟 2：選擇地圖顏色維度 ─────────────────────────────────
color_by = st.radio(
    "顏色依據",
    ["行政區（sarea）", "可借車數（available_rent_bikes）"],
    horizontal=True,
)
color_col = "sarea" if "sarea" in color_by else "available_rent_bikes"

col1, col2 = st.columns([1, 3])
with col1:
    st.dataframe(
        stations[["站名", "sarea", "available_rent_bikes", "Quantity"]]
        .sort_values("available_rent_bikes", ascending=False)
        .head(20),
        use_container_width=True,
    )

with col2:
    # ── 步驟 3：散點地圖 ──────────────────────────────────────
    fig = px.scatter_mapbox(
        stations,
        lat="latitude",                   # 緯度欄
        lon="longitude",                  # 經度欄
        color=color_col,                  # 顏色欄位
        size="available_rent_bikes",      # 點的大小 = 可借車數
        size_max=20,
        hover_name="站名",                # 懸停顯示主標題
        hover_data={                      # 懸停顯示的額外欄位
            "sarea":                   True,    # 行政區
            "available_rent_bikes":    True,    # 可借車數
            "available_return_bikes":  True,    # 空位數
            "Quantity":                True,    # 總停車格
            "ar":                      True,    # 地址
            "latitude":                False,   # 不顯示座標
            "longitude":               False,
        },
        mapbox_style="open-street-map",   # 免費底圖，不需 API key
        zoom=11,
        center={"lat": 25.065, "lon": 121.542},
        height=560,
        color_continuous_scale="YlOrRd",
        title="YouBike 2.0 台北市站點分布",
    )
    fig.update_layout(margin={"r": 0, "t": 30, "l": 0, "b": 0})
    st.plotly_chart(fig, use_container_width=True)

st.info("""
**改改看：**
- `mapbox_style` 換成 `"carto-positron"` 或 `"carto-darkmatter"`（不同底圖風格）
- `zoom=11` 改成 `zoom=13`，放大到街道級別
- `size="available_rent_bikes"` 改成 `size="Quantity"`，點大小改用總停車格數
- 把 `color_col` 固定成 `"sarea"`，再加一個 `min_bikes` 滑桿過濾可借車數
""")
