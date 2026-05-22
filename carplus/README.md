# CarPlus Smart2Go 營運分析儀表板

基於 CarPlus Smart2Go 共享車資料的互動式 Streamlit Dashboard，提供地理分布、需求分析、供需比較等視覺化功能。支援本機（讀取 CSV）與雲端（BigQuery + Cloud Run）兩種部署方式。

---

## 專案結構

```
.
├── dashboard.py              # 本機版（讀取 CSV）
├── dashboard_bigquery.py     # 雲端版（讀取 BigQuery）
├── requirements.txt          # Python 依賴（Cloud Run 用）
├── Dockerfile                # Cloud Run 容器定義
├── .dockerignore
├── schema.md                 # 資料欄位定義
├── orders.csv
├── parking_lots.csv
├── available_cars.csv
└── map_browsing.csv
```

---

## 資料集說明

| 資料表 | 筆數 | 說明 |
|---|---|---|
| `orders.csv` | ~135K | 訂單（取還車時間、站點、車款、里程） |
| `parking_lots.csv` | ~960 | 站點基本資料（含經緯度、城市、業務類型） |
| `available_cars.csv` | ~560萬 | 各站點逐小時可用車數 |
| `map_browsing.csv` | ~146萬 | App 地圖頁瀏覽流量（需求代理指標） |

欄位詳細定義請見 [schema.md](schema.md)。

---

## Dashboard 功能

| 分頁 | 內容 |
|---|---|
| 📊 **總覽** | KPI 指標、月訂單趨勢、熱門車款、24小時分布、星期分布 |
| 🗺️ **地理分布** | 站點熱度地圖（可切換訂單數/城市著色）、城市與行政區佔比、業務類型分析 |
| 📈 **需求分析** | 訂單與 App 瀏覽熱力圖（星期×小時）、每日供需趨勢（7日均線）、逐小時供需對比、瀏覽→訂單轉換率、租借時長與里程分布 |
| 🔍 **站點深探** | 選擇任一站點，查看逐小時訂單、供需對比、App 瀏覽對比、月趨勢、熱門異地還車站點 |

左側 Sidebar 提供城市篩選與日期範圍過濾，所有圖表同步更新。

---

## 本機執行（CSV 版）

### 安裝依賴

```bash
pip install streamlit plotly pandas
```

### 啟動

```bash
cd "/path/to/NTHU CarPlus Smart2Go"
python3 -m streamlit run dashboard.py
```

瀏覽器開啟 http://localhost:8501

---

## 雲端部署（BigQuery + Cloud Run）

### 前置條件

- GCP 專案已啟用 BigQuery API 與 Cloud Run API
- 四張資料表已上傳至 BigQuery（欄位需符合 `schema.md`）
- 已安裝 `gcloud` CLI 並登入（`gcloud auth login`）

### 1. 將 CSV 上傳至 BigQuery

```bash
export PROJECT=your-project-id
export DATASET=carplus_smart2go

# 建立資料集
bq mk --dataset ${PROJECT}:${DATASET}

# 上傳四張表（自動偵測 schema）
for TABLE in orders parking_lots available_cars map_browsing; do
  bq load \
    --autodetect \
    --source_format=CSV \
    --skip_leading_rows=1 \
    ${PROJECT}:${DATASET}.${TABLE} \
    ${TABLE}.csv
done
```

### 2. 建立 Service Account 並授權

```bash
# 建立 SA
gcloud iam service-accounts create carplus-dashboard \
  --display-name="CarPlus Dashboard"

# 授予 BigQuery 讀取權限
gcloud projects add-iam-policy-binding ${PROJECT} \
  --member="serviceAccount:carplus-dashboard@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ${PROJECT} \
  --member="serviceAccount:carplus-dashboard@${PROJECT}.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### 3. Build & Push 容器映像

```bash
# 使用 Cloud Build（不需本機 Docker）
gcloud builds submit \
  --tag gcr.io/${PROJECT}/carplus-dashboard \
  "/path/to/NTHU CarPlus Smart2Go"
```

### 4. 部署至 Cloud Run

```bash
gcloud run deploy carplus-dashboard \
  --image gcr.io/${PROJECT}/carplus-dashboard \
  --platform managed \
  --region asia-east1 \
  --set-env-vars GCP_PROJECT_ID=${PROJECT},BQ_DATASET=${DATASET} \
  --service-account carplus-dashboard@${PROJECT}.iam.gserviceaccount.com \
  --memory 1Gi \
  --allow-unauthenticated
```

部署完成後，`gcloud run deploy` 會輸出服務 URL。

### 環境變數

| 變數 | 必填 | 說明 |
|---|---|---|
| `GCP_PROJECT_ID` | ✅ | GCP 專案 ID |
| `BQ_DATASET` | 否 | BigQuery 資料集名稱（預設：`carplus_smart2go`） |

### 本機測試 BigQuery 版

```bash
# 1. 設定 Application Default Credentials
gcloud auth application-default login

# 2. 設定環境變數後啟動
export GCP_PROJECT_ID=your-project-id
export BQ_DATASET=carplus_smart2go

python3 -m streamlit run dashboard_bigquery.py
```

---

## 架構說明（BigQuery 版效能優化）

`available_cars`（560萬筆）與 `map_browsing`（146萬筆）資料量大，直接全表載入成本高。BigQuery 版在 SQL 層完成聚合，僅傳輸結果：

| 用途 | SQL 聚合策略 |
|---|---|
| 熱力圖 | `GROUP BY dow, click_hour` |
| 每日趨勢圖 | `GROUP BY date`，限定日期範圍 |
| 逐小時供需圖 | `GROUP BY available_hour` |
| 站點深探 | `WHERE parking_lot_id = @station_id` 後再聚合 |

所有查詢結果以 `@st.cache_data(ttl=3600)` 快取一小時，避免重複查詢 BigQuery。
