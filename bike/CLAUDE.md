# CLAUDE.md — 共享單車儀表板專案說明

本檔案讓 Claude Code 了解此專案的架構與慣例，以便更精確地協助學生修改儀表板。

---

## 專案概覽

- **語言**：Python 3.10+
- **框架**：Streamlit（互動 UI）+ Plotly（圖表）
- **主程式**：`dashboard.py`（單一檔案架構，所有邏輯集中於此）
- **用途**：共享單車營運分析，結合真實 YouBike 2.0 站點資料與模擬訂單資料

---

## 目錄結構

```
bike/
├── dashboard.py              # 主程式（唯一需要修改的程式檔）
├── data/
│   ├── parking_lots_real.csv # 真實站點資料（JSON 格式，1,758 站）
│   ├── parking_lots.csv      # 模擬站點（60 站，S0001–S0060，供訂單 Join）
│   ├── orders.csv            # 模擬借還車訂單
│   ├── available_cars.csv    # 模擬每小時可用車輛數
│   └── map_browsing.csv      # 模擬 App 地圖點擊紀錄
└── README.md
```

---

## 資料架構（重要）

此專案採**混合架構**，因兩份站點資料的 ID 格式不同：

| 資料集 | 站點 ID 格式 | 用途 |
|--------|------------|------|
| `parking_lots_real.csv` | `500101001`（YouBike 官方） | 地圖顯示、場域分析 |
| `parking_lots.csv` | `S0001`–`S0060`（模擬） | 訂單 Join，維持 city/area 欄位 |

**結論：兩份資料 ID 無法互相 Join，請勿嘗試合併。**

---

## 全域變數（在所有 tab 都可使用）

| 變數名 | 型別 | 說明 |
|--------|------|------|
| `orders` | DataFrame | 原始訂單，含 `duration_min`、`hour`、`dow`、`date`、`month`、`is_round_trip` 衍生欄 |
| `parking_lots` | DataFrame | 模擬站點（60 站），欄位見下方 |
| `real_stations` | DataFrame | 真實 YouBike 站點（已過濾停用站），含即時可借/空位數 |
| `available_cars` | DataFrame | 每小時可用車輛，含 `dow` 衍生欄 |
| `map_browsing` | DataFrame | App 點擊紀錄，含 `dow` 衍生欄 |
| `orders_geo` | DataFrame | `orders` left join `parking_lots`，含 city/area/biz_type 欄位 |
| `fo` | DataFrame | 經 sidebar 篩選後的 `orders_geo`（**分析時請使用 `fo`，不要用 `orders_geo`**） |

### parking_lots / real_stations 共用欄位

```
parking_lot_id, parking_lot_name, parking_lot_city, parking_lot_area,
parking_lot_longitude, parking_lot_latitude, parking_lot_biz_type_desc,
min_rent_start_date, max_rent_start_date
```

### real_stations 額外欄位

```
available_rent_bikes, available_return_bikes, total_slots, address, is_active
```

---

## 儀表板結構

```
sidebar  →  城市篩選 + 日期範圍  →  產生 fo（篩選後訂單）

tab1  總覽         →  fo
tab2  地理分布     →  real_stations（地圖）+ fo（city/area 圖）
tab3  需求分析     →  fo + available_cars + map_browsing
tab4  站點深探     →  fo（依站點過濾）+ available_cars + map_browsing
```

---

## 常用 Plotly Express 圖表對照

| 圖表類型 | 函式 | 典型用法 |
|---------|------|---------|
| 長條圖 | `px.bar()` | 類別比較 |
| 橫向長條 | `px.bar(..., orientation="h")` | 排名清單 |
| 折線/面積 | `px.line()` / `px.area()` | 時間趨勢 |
| 圓餅/環形 | `px.pie(..., hole=0.4)` | 佔比 |
| 散點地圖 | `px.scatter_mapbox()` | 地理分布 |
| 熱力圖 | `px.imshow()` | pivot 矩陣 |
| 直方圖 | `px.histogram()` | 數值分布 |
| 雙軸圖 | `make_subplots(specs=[[{"secondary_y": True}]])` | 供需對比 |

---

## 程式慣例

1. **所有圖表** 最後都呼叫 `st.plotly_chart(fig, use_container_width=True)`
2. **多欄排版** 用 `col1, col2 = st.columns(2)` + `with col1:` 區塊
3. **分頁** 用 `with tab1:` 區塊，tab 變數在 `st.tabs([...])` 解包
4. **資料載入** 全部用 `@st.cache_data` 避免重複讀取
5. **新增欄位** 在 load 函式內完成，不要在 tab 區塊裡修改 DataFrame
6. **顏色風格** 連續色階用 `"Blues"` / `"YlOrRd"` / `"Viridis"`；離散色用 `color_discrete_sequence=["#667eea"]`

---

## 常見錯誤與提示

- `fo` 可能因篩選後為空 → 加 `if len(fo) == 0: st.warning("無資料"); st.stop()` 保護
- `groupby` 結果若 index 不連續，`pivot` 前先 `.reset_index()`
- `px.scatter_mapbox` 需要 `mapbox_style`，使用 `"open-street-map"` 不需要 token
- 日期欄位 `date` 是 `pd.Timestamp`，與 sidebar 的 `datetime.date` 比較時用 `.dt.date`
- `real_stations` 的 `parking_lot_id` 是字串型別（`str`）

---

## 學生作業常見改動範圍

1. 在既有 tab 內**新增一個圖表區塊**（最常見）
2. 在 sidebar **新增一個篩選條件**
3. **新增一個 tab**（複製現有 tab 結構再修改）
4. 將某張圖的顏色欄位或指標換成不同欄位
5. 在 Tab 2 地圖加入新的 `hover_data` 欄位
