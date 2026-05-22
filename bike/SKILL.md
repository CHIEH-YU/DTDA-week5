# SKILL.md — 儀表板改動技能手冊

本文件提供學生在修改 `dashboard.py` 時最常需要的操作範本。  
每個 Skill 都包含：**什麼時候用** / **在哪裡加** / **程式碼模板**。

---

## Skill 1 — 新增指標卡（Metric）

**何時用**：在頁面頂端展示單一數字 KPI。

**在哪裡加**：任何 `with tab?:` 區塊內，先用 `st.columns()` 分欄。

```python
c1, c2, c3 = st.columns(3)
c1.metric("標題",  "數值字串",  delta="變化量（選填）")

# 範例：用 fo 計算
c1.metric("平均里程", f"{fo['mileage_diff'].mean():.2f} 公里")
c2.metric("最長租借", f"{fo['duration_min'].max():.0f} 分鐘")
c3.metric("單程比例", f"{(~fo['is_round_trip']).mean()*100:.1f}%")
```

---

## Skill 2 — 新增長條圖

**何時用**：比較各類別的數量或指標。

```python
# 1. 先 groupby 算出數值
df_plot = (
    fo.groupby("car_series_name")          # 依車款分組
    .agg(次數=("order_no", "count"),
         平均里程=("mileage_diff", "mean"))
    .reset_index()
    .sort_values("次數", ascending=False)
    .head(10)
)

# 2. 畫圖
fig = px.bar(
    df_plot,
    x="car_series_name",
    y="次數",
    title="各車款借車次數",
    color="次數",
    color_continuous_scale="Blues",
)
fig.update_layout(coloraxis_showscale=False, xaxis_title="車款")
st.plotly_chart(fig, use_container_width=True)
```

**橫向版（適合長標籤）**：加 `orientation="h"`，並把 `x` / `y` 欄位對調。

---

## Skill 3 — 新增折線圖（時間趨勢）

**何時用**：觀察指標隨日期 / 月份的變化。

```python
daily = fo.groupby("date").size().reset_index(name="借車次數")

fig = px.line(
    daily,
    x="date",
    y="借車次數",
    title="每日借車趨勢",
    color_discrete_sequence=["#e74c3c"],
)
fig.update_layout(xaxis_title="日期", yaxis_title="借車次數")
st.plotly_chart(fig, use_container_width=True)
```

**加 7 日滾動平均**：

```python
daily["7日均"] = daily["借車次數"].rolling(7).mean()
fig = px.line(daily, x="date", y=["借車次數", "7日均"], title="每日趨勢含均線")
```

---

## Skill 4 — 新增圓餅 / 環形圖

**何時用**：展示各類別佔整體的比例。

```python
df_pie = fo.groupby("parking_lot_biz_type_desc").size().reset_index(name="次數")

fig = px.pie(
    df_pie,
    values="次數",
    names="parking_lot_biz_type_desc",
    title="各場域類型借車佔比",
    hole=0.4,          # 0 = 實心圓餅；0.4 = 環形
)
st.plotly_chart(fig, use_container_width=True)
```

---

## Skill 5 — 新增直方圖（數值分布）

**何時用**：觀察連續數值（里程、時長）的分布形狀。

```python
fig = px.histogram(
    fo[fo["mileage_diff"].between(0, 20)],   # 過濾極端值
    x="mileage_diff",
    nbins=40,
    title="騎乘里程分布",
    color_discrete_sequence=["#667eea"],
)
fig.update_layout(xaxis_title="公里", yaxis_title="次數")
st.plotly_chart(fig, use_container_width=True)
```

---

## Skill 6 — 新增熱力圖（Heatmap）

**何時用**：展示兩個類別維度（如星期 × 小時）的數量矩陣。

```python
hm = fo.groupby(["dow", "hour"]).size().reset_index(name="借車次數")
pivot = hm.pivot(index="dow", columns="hour", values="借車次數").fillna(0)
pivot.index = [DOW_MAP[i] for i in pivot.index]   # 數字轉中文星期

fig = px.imshow(
    pivot,
    labels=dict(x="小時", y="星期", color="借車次數"),
    title="借車熱力圖",
    color_continuous_scale="YlOrRd",
    aspect="auto",
)
st.plotly_chart(fig, use_container_width=True)
```

---

## Skill 7 — 新增雙軸圖（供需對比）

**何時用**：兩條數列量級差距大，或單位不同（如「車輛數」vs「借車次數」）。

```python
from plotly.subplots import make_subplots
import plotly.graph_objects as go

fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.add_trace(
    go.Bar(x=df["hour"], y=df["平均可用車數"],
           name="平均可用車數", marker_color="rgba(52,152,219,0.6)"),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=df["hour"], y=df["借車次數"],
               name="借車次數", line=dict(color="#e74c3c", width=2.5)),
    secondary_y=True,
)
fig.update_layout(title="供需對比", hovermode="x unified",
                  xaxis=dict(title="小時", tickmode="linear", dtick=2))
fig.update_yaxes(title_text="平均可用車數", secondary_y=False)
fig.update_yaxes(title_text="借車次數",   secondary_y=True)
st.plotly_chart(fig, use_container_width=True)
```

---

## Skill 8 — Sidebar 新增篩選器

**在哪裡加**：`st.sidebar.markdown("---")` 之後，`fo = orders_geo[mask].copy()` 之前。

### 下拉選單（Selectbox）

```python
biz_types = ["全部"] + sorted(orders_geo["parking_lot_biz_type_desc"].dropna().unique())
selected_biz = st.sidebar.selectbox("場域類型篩選", biz_types)

# 加入 mask
if selected_biz != "全部":
    mask &= orders_geo["parking_lot_biz_type_desc"] == selected_biz
```

### 多選框（Multiselect）

```python
car_options = sorted(orders["car_series_name"].dropna().unique())
selected_cars = st.sidebar.multiselect("車款篩選", car_options, default=car_options)

if selected_cars:
    mask &= orders_geo["car_series_name"].isin(selected_cars)
```

### 數值滑桿（Slider）

```python
max_km = float(orders["mileage_diff"].quantile(0.99))
km_range = st.sidebar.slider("里程範圍（公里）", 0.0, max_km, (0.0, max_km), 0.5)
mask &= orders_geo["mileage_diff"].between(km_range[0], km_range[1])
```

---

## Skill 9 — 新增分頁（Tab）

**在哪裡加**：找到 `tab1, tab2, tab3, tab4 = st.tabs([...])` 這一行，加入新 tab。

```python
# 修改前
tab1, tab2, tab3, tab4 = st.tabs(["📊 總覽", "🗺️ 地理分布", "📈 需求分析", "🔍 站點深探"])

# 修改後（新增第五個 tab）
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 總覽", "🗺️ 地理分布", "📈 需求分析", "🔍 站點深探", "🚴 用戶分析"
])

# 在最後新增
with tab5:
    st.subheader("用戶行為分析")
    # ... 你的圖表 ...
```

---

## Skill 10 — 在地圖 Hover 加入新欄位

**何時用**：想讓使用者把滑鼠移到地圖點時，看到更多站點資訊。

```python
# 在 px.scatter_mapbox 的 hover_data 字典裡新增欄位：
hover_data={
    "parking_lot_area":          True,          # 顯示，欄位名稱為 label
    "available_rent_bikes":      True,
    "available_return_bikes":    True,
    "total_slots":               True,
    "address":                   True,
    # 格式化數字：
    "某數值欄位":                ":.1f",        # 小數點一位
    # 隱藏（不顯示在 hover）：
    "parking_lot_longitude":     False,
},
```

> `hover_data` 的 key 必須是 DataFrame 裡存在的欄位名稱。

---

## Skill 11 — 顯示資料表（DataFrame）

**何時用**：讓使用者直接看到原始數據，或排行榜清單。

```python
# 前 N 名排行
top = (
    fo.groupby("depart_parking_lot_id")
    .size()
    .reset_index(name="借車次數")
    .sort_values("借車次數", ascending=False)
    .head(20)
)
st.dataframe(top, use_container_width=True, hide_index=True)

# 可搜尋、可排序的互動表格（Streamlit 1.23+）
st.dataframe(
    top.style.background_gradient(subset=["借車次數"], cmap="Blues"),
    use_container_width=True,
)
```

---

## Skill 12 — 使用 real_stations 真實站點資料

**何時用**：想分析**目前即時**的可借車、空位、站點分布。

```python
# real_stations 可用欄位：
# parking_lot_id, parking_lot_name, parking_lot_area,
# parking_lot_biz_type_desc, parking_lot_longitude, parking_lot_latitude,
# available_rent_bikes, available_return_bikes, total_slots, address

# 範例：找出目前可借車最多的 10 站
top_avail = (
    real_stations[["parking_lot_name", "parking_lot_area",
                   "available_rent_bikes", "total_slots"]]
    .sort_values("available_rent_bikes", ascending=False)
    .head(10)
)
st.dataframe(top_avail, use_container_width=True, hide_index=True)

# 計算各行政區平均可借率
area_rate = (
    real_stations.groupby("parking_lot_area")
    .apply(lambda d: d["available_rent_bikes"].sum() / d["total_slots"].sum() * 100)
    .reset_index(name="可借率(%)")
    .sort_values("可借率(%)", ascending=False)
)
fig = px.bar(area_rate, x="parking_lot_area", y="可借率(%)",
             title="各行政區目前平均可借率", color="可借率(%)",
             color_continuous_scale="RdYlGn")
st.plotly_chart(fig, use_container_width=True)
```

> **注意**：`real_stations` 與 `fo`（訂單）的 `parking_lot_id` 格式不同，**不能直接 merge**。

---

## 常用 Debug 技巧

```python
# 在任何地方臨時印出 DataFrame 內容
st.write(fo.head())
st.write(fo.dtypes)
st.write(fo.describe())

# 確認 groupby 結果
st.write(fo.groupby("parking_lot_city").size())
```

> 確認沒問題後記得把 `st.write(...)` 移除。
