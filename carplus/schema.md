# 資料集 Schema 定義

本文件定義共享車的 4 張核心資料表結構。

---

## 1. 站點資料表 (`parking_lots.csv`)
描述站點的基礎資訊與地理座標。

| 欄位名稱 | 資料型態 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| `parking_lot_id` | `VARCHAR` | 站點唯一識別碼 | **Primary Key** |
| `parking_lot_name` | `VARCHAR` | 站點名稱 | **重要：** 若名稱含「路邊」字串（如: 格上-板橋區(路邊)-調），代表該站點為「虛擬區域站點」，經緯度僅為區域代表點，實際租還於該區域內合法路邊停車格。 | |
| `parking_lot_city` | `VARCHAR` | 站點所屬城市 | |
| `parking_lot_area` | `VARCHAR` | 站點所屬行政區 | |
| `parking_lot_longitude`| `DECIMAL` | 站點經度 | |
| `parking_lot_latitude` | `DECIMAL` | 站點緯度 | |
| `parking_lot_biz_type_desc` | `VARCHAR` | 業務類型說明 | **邏輯如下：**<br>1. **甲租甲還**：同站租還站點。<br>2. **甲租乙還**、**聰明租還**：異站租還站點。 |
| `min_rent_start_date` | `DATE` | 該站點第一筆交易紀錄出車日期 | |
| `max_rent_start_date` | `DATE` | 該站點最後一筆交易紀錄出車日期 | |
| `data_group` | `VARCHAR` | 資料分組標籤 | 此欄值皆為 [TRAIN] |

---

## 2. 訂單資料表 (`orders.csv`)
記錄使用者實際的租借與還車交易資訊。

| 欄位名稱 | 資料型態 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| `order_no` | `VARCHAR` | 訂單編號 | **Primary Key** |
| `acct_id` | `VARCHAR` | 使用者帳號 ID | |
| `booking_dt` | `DATETIME` | 預約時間 | |
| `rent_start_dt` | `DATETIME` | 實際取車時間 | |
| `rent_end_dt` | `DATETIME` | 實際還車時間 | |
| `depart_parking_lot_id`| `VARCHAR` | 取車站點 ID | **FK** (Ref: `parking_lots`) |
| `return_parking_lot_id`| `VARCHAR` | 還車站點 ID | **FK** (Ref: `parking_lots`) |
| `car_series_name` | `VARCHAR` | 車款 | |
| `mileage_diff` | `INT` | 行駛里程差異 | 單位為公里|

---

## 3. 可用車資料表 (`available_cars.csv`)
記錄各時段站點的車輛供給情況。

| 欄位名稱 | 資料型態 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| `parking_lot_id` | `VARCHAR` | 站點 ID | **Composite PK** / **FK** |
| `available_date` | `DATE` | 可用日期 | **Composite PK** |
| `available_hour` | `INT` | 可用小時 (0-23) | **Composite PK** |
| `available_cars` | `INT` | 該時段可用車輛數 | |

**資料特性說明：**
* 本表**不包含**車輛供給數為零（`available_cars = 0`）的時段與站點記錄。
---

## 4. App 瀏覽地圖頁之流量資料表 (`map_browsing.csv`)
記錄使用者在 GoSmart App 上進入共享車地圖首頁的行為流量，通常作為需求預測的特徵。

| 欄位名稱 | 資料型態 | 說明 | 備註 |
| :--- | :--- | :--- | :--- |
| `parking_lot_id` | `VARCHAR` | 站點 ID | **Composite PK** / **FK** |
| `click_date` | `DATE` | 點擊日期 | **Composite PK** |
| `click_hour` | `INT` | 點擊小時 (0-23) | **Composite PK** |
| `num_click_times` | `INT` | 總點擊次數 | |
| `num_click_users` | `INT` | 點擊不重複人數 | |

**資料特性說明：**
* **GPS 定位邏輯：** 此流量僅包含「成功判定站點位置」的紀錄。使用者進入地圖時需開啟 GPS，系統方能判斷其最近站點並記錄於此表；若未開啟 GPS 或無法判定站點，則不計入此表。