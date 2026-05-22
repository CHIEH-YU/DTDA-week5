# 台灣共享單車營運分析儀表板

這是一份給課堂使用的完整練習專案，主題是「共享單車數據分析」。學生會從個別圖表練習出發，最終理解一個完整的 Streamlit 互動式儀表板是如何組裝起來的。

專案採**混合資料架構**：地圖使用 **真實 YouBike 2.0 台北市站點**，訂單行為分析使用**模擬假資料**，兼顧示範真實場景與可公開執行。

課堂比喻：

| 調度室角色 | 技術角色 | 本專案中的例子 |
|---|---|---|
| 派車人員 | 前端使用者 | 在 sidebar 選擇行政區、日期範圍 |
| 顯示看板 | Streamlit 儀表板 | `dashboard.py` 的四個分頁 |
| 路線規劃師 | Plotly 視覺化 | `px.bar`、`px.imshow`、`go.Figure` |
| 停車格感測器 | 資料來源 | `available_cars.csv`、`map_browsing.csv` |
| 調度紀錄簿 | DataFrame（pandas） | `orders`、`fo`（篩選後）、`real_stations` |

> 本專案使用合成假資料，僅供教學示範，不代表任何真實營運紀錄或個人資料。

---

## 0. 專案結構

```text
bike/
├── README.md
├── CLAUDE.md                   # Claude Code 使用說明（給 AI 輔助開發用）
├── SKILL.md                    # 本專案技術技能說明
├── dashboard.py                # 主程式（完整儀表板）
├── generate_fake_data.py       # 重新生成模擬資料
├── data/
│   ├── orders.csv              # 模擬借還車訂單（20,000 筆）
│   ├── orders_real.json        # 真實 YouBike 2.0 台北市站點快照（1,758 站）
│   ├── available_cars.csv      # 模擬每小時可用車輛數（423,000 筆）
│   ├── map_browsing.csv        # 模擬 App 地圖點擊紀錄（423,000 筆）
│   └── parking_lots.csv        # 模擬站點（60 站，S0001–S0060）
├── chart_exercises/            # 單圖練習題（16 題）
│   ├── 01_月借車趨勢_長條圖.py
│   ├── 02_熱門車款_水平長條圖.py
│   ├── 03_24小時分布_區域圖.py
│   ├── 04_星期別分布_長條圖.py
│   ├── 05_城市佔比_圓餅圖.py
│   ├── 06_熱門行政區_水平長條圖.py
│   ├── 07_場域類型_長條圖與圓餅圖.py
│   ├── 08_訂單熱力圖_星期x小時.py
│   ├── 09_App瀏覽熱力圖_星期x小時.py
│   ├── 10_每日供需趨勢_雙軸折線圖.py
│   ├── 11_逐小時供需對比_複合圖.py
│   ├── 12_瀏覽轉換率_長條圖.py
│   ├── 13_租借時長_直方圖.py
│   ├── 14_騎乘里程_直方圖.py
│   ├── 15_站點地圖_散點地圖.py
│   └── 16_站點深探_互動下拉選單.py
└── cloudrun/                   # Streamlit Community Cloud / Cloud Run 部署用
    ├── Dockerfile
    ├── requirements.txt
    ├── cloudbuild.yaml
    ├── dashboard.py
    └── data/                   # 與上方 data/ 相同內容
```

---

## 1. 環境設定

建議使用 Python 3.10 以上。

### macOS / Linux

```bash
cd bike
python3 -m venv .venv
source .venv/bin/activate
pip install streamlit pandas plotly
```

### Windows PowerShell

```powershell
cd bike
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install streamlit pandas plotly
```

---

## 2. 啟動儀表板

```bash
streamlit run dashboard.py
```

預期看到：

```text
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

瀏覽器會自動開啟，或手動前往 `http://localhost:8501`。

---

## 3. 資料說明

| 檔案 | 來源 | 筆數 | 說明 |
|---|---|---|---|
| `orders_real.json` | [台北市政府開放資料](https://data.taipei/dataset/detail?id=c6bc8aed-557d-41d5-bfb1-8da24f78f2fb) | 1,758 站 | YouBike 2.0 即時站點快照，含座標、可借車數、空位數 |
| `orders.csv` | 模擬 | 20,000 筆 | 借還車訂單，含取還車站、騎乘時長、里程、車款 |
| `available_cars.csv` | 模擬 | 423,000 筆 | 前 150 大站逐小時可用車輛數（每 7 天取樣）|
| `map_browsing.csv` | 模擬 | 423,000 筆 | App 地圖點擊紀錄，模擬使用者查站行為 |
| `parking_lots.csv` | 模擬 | 60 站 | 虛構站點（S0001–S0060），供訂單 Join 用 |

### 混合架構說明

| 資料集 | 站點 ID 格式 | 用途 |
|---|---|---|
| `orders_real.json` | `500101001`（YouBike 官方） | Tab 2 地圖顯示、場域統計 |
| `parking_lots.csv` | `S0001`–`S0060`（模擬） | Tab 1/3/4 訂單行為分析 |

> **重要**：兩份站點 ID 格式不同，無法互相 Join，儀表板以此設計刻意區分「地圖呈現」與「行為分析」兩條資料線。

### 場域類型推導規則

`parking_lot_biz_type_desc` 由站名關鍵字自動判斷：

| 場域類型 | 判斷關鍵字 |
|---|---|
| 捷運站周邊 | 捷運、MRT |
| 大學校園 | 大學、學院、學校、University |
| 公園綠地 | 公園、植物園、綠地 |
| 購物商圈 | 商圈、市場、百貨、Mall |
| 觀光景點 | 景點、觀光、博物館、Museum |
| 住宅社區 | （其餘預設） |

---

## 4. 儀表板功能

| 分頁 | 內容 | 主要資料來源 |
|---|---|---|
| 📊 總覽 | 5 個 KPI 指標卡、月借車趨勢、熱門車款 Top 10、24 小時分布、星期別分布 | `orders` |
| 🗺️ 地理分布 | YouBike 真實站點互動地圖、行政區佔比圓餅圖、Top 15 行政區、場域類型分析 | `orders_real.json` + `orders` |
| 📈 需求分析 | 借車 & 瀏覽熱力圖、每日供需雙軸折線圖（7 日均線）、逐小時供需複合圖、轉換率、時長 & 里程直方圖 | `orders` + `available_cars` + `map_browsing` |
| 🔍 站點深探 | 單站借車時段分布、供需對比、App 瀏覽 vs 借車、月趨勢、還車目的地 Top 10 | `orders` + `available_cars` + `map_browsing` |

### Sidebar 篩選器

| 控制項 | 說明 |
|---|---|
| 行政區篩選 | 限定特定行政區（預設：全部） |
| 場域類型篩選 | 限定站點類型（預設：全部） |
| 日期範圍 | 選取分析期間（可拖拉縮短範圍） |

篩選後的訂單存入全域變數 `fo`，所有分頁圖表均使用 `fo`。

---

## 5. 圖表練習（chart_exercises/）

16 個獨立 Streamlit 小程式，每支對應儀表板中的一張圖。從資料讀取到 Plotly 呈現，每個步驟都有中文註解說明。

| 題號 | 檔案 | 圖表類型 | 學習重點 |
|---|---|---|---|
| 01 | `01_月借車趨勢_長條圖.py` | `px.bar` | `dt.to_period`、groupby size |
| 02 | `02_熱門車款_水平長條圖.py` | `px.bar (h)` | value_counts、orientation |
| 03 | `03_24小時分布_區域圖.py` | `px.area` | dt.hour、color_discrete_sequence |
| 04 | `04_星期別分布_長條圖.py` | `px.bar` | DOW_MAP、自訂 x 軸標籤 |
| 05 | `05_城市佔比_圓餅圖.py` | `px.pie` | hole、values/names 參數 |
| 06 | `06_熱門行政區_水平長條圖.py` | `px.bar (h)` | sort_values、head(N) |
| 07 | `07_場域類型_長條圖與圓餅圖.py` | `px.bar` + `px.pie` | 同資料雙圖呈現 |
| 08 | `08_訂單熱力圖_星期x小時.py` | `px.imshow` | pivot、fillna、aspect |
| 09 | `09_App瀏覽熱力圖_星期x小時.py` | `px.imshow` | 跨 DataFrame 相同結構比較 |
| 10 | `10_每日供需趨勢_雙軸折線圖.py` | `go.Scatter` | rolling(7).mean、yaxis2 |
| 11 | `11_逐小時供需對比_複合圖.py` | `go.Bar` + `go.Scatter` | make_subplots、secondary_y |
| 12 | `12_瀏覽轉換率_長條圖.py` | `px.bar` | 計算轉換率、merge |
| 13 | `13_租借時長_直方圖.py` | `px.histogram` | between、nbins |
| 14 | `14_騎乘里程_直方圖.py` | `px.histogram` | 極端值過濾 |
| 15 | `15_站點地圖_散點地圖.py` | `px.scatter_mapbox` | lat/lon、hover_data、open-street-map |
| 16 | `16_站點深探_互動下拉選單.py` | 多圖 + `st.selectbox` | format_func、互動式篩選 |

執行單一練習：

```bash
cd chart_exercises
streamlit run 01_月借車趨勢_長條圖.py
```

---

## 6. 重新生成模擬資料

若需要重新產生 `orders.csv`、`available_cars.csv`、`map_browsing.csv`（`orders_real.json` 為真實資料快照，不需重新生成）：

```bash
pip install pandas numpy
python generate_fake_data.py
```

成功時看到：

```text
載入真實站點資料 …
  → 啟用站點：1,758 站
生成 orders.csv（20,000 筆）…
  → 20,000 筆訂單寫入 orders.csv
生成 available_cars.csv（前 150 大站，每 7 天取樣）…
  → 423,000 筆記錄寫入 available_cars.csv
生成 map_browsing.csv（前 150 大站，每 7 天取樣）…
  → 423,000 筆記錄寫入 map_browsing.csv
✅ 完成！
```

### 更新真實站點資料

`orders_real.json` 是台北市政府開放資料的快照。如需抓取最新即時站點：

```bash
curl -o data/orders_real.json \
  "https://tcgbusfs.blob.core.windows.net/dotapp/youbike/v2/youbike_immediate.json"
```

重啟 Streamlit 後快取自動重建（`@st.cache_data` 會失效並重新載入）。

---

## 7. 部署到 Streamlit Community Cloud（免費）

`cloudrun/` 資料夾已包含所有部署所需檔案（`dashboard.py`、`requirements.txt`、`data/`）。

**Step 1：把 `cloudrun/` 內容推到 GitHub**

```bash
cd cloudrun
git init
git add .
git commit -m "init bike dashboard"
git remote add origin https://github.com/你的帳號/bike-dashboard.git
git push -u origin main
```

**Step 2：前往 [share.streamlit.io](https://share.streamlit.io)**

1. 用 GitHub 帳號登入
2. New app → 選剛才建立的 repo
3. Branch：`main`
4. Main file path：`dashboard.py`
5. 點 **Deploy**，約 2 分鐘後上線

> 如果整個 `bike/` 資料夾作為 repo，Main file path 填 `cloudrun/dashboard.py`。

### 進階：Google Cloud Run 部署

`cloudrun/` 內也提供 `Dockerfile` 和 `cloudbuild.yaml`，可直接連接 GitHub 透過 Cloud Build 自動部署到 Cloud Run。詳情請見 `cloudrun/cloudbuild.yaml` 內的注解。

---

## 8. 常見錯誤排查

| 問題 | 常見原因 | 解法 |
|---|---|---|
| `ModuleNotFoundError: streamlit` | 忘記啟動 venv 或未安裝 | `source .venv/bin/activate` 後 `pip install streamlit pandas plotly` |
| `FileNotFoundError: orders.csv` | 在錯誤目錄執行 | 確認在 `bike/` 目錄下執行 `streamlit run dashboard.py` |
| `FileNotFoundError: orders_real.json` | data 資料夾缺檔 | 重新 clone 或執行 `python generate_fake_data.py` |
| 地圖空白 / 無法顯示 | mapbox token 問題 | 本專案使用 `open-street-map`，不需 token，確認 plotly 版本 ≥ 5.0 |
| chart_exercises 找不到資料 | 路徑計算錯誤 | 練習題用 `pathlib.Path(__file__).parent.parent / "data"`，需在 `chart_exercises/` 目錄或上層執行 |
| Streamlit Community Cloud 部署失敗 | requirements.txt 找不到 | 確認 `requirements.txt` 與 `dashboard.py` 在同一層 |
| `KeyError: 'parking_lot_area'` | sidebar 篩選後 `fo` 為空 | 先確認日期範圍有資料，或行政區 / 場域類型篩選太嚴格 |
