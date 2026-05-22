"""
generate_fake_data.py
─────────────────────
以真實 YouBike 2.0 站點（orders_real.json）為基礎，
延伸生成與 dashboard.py 完全相容的假資料。

生成檔案（輸出至 data/）：
  - orders.csv          借還車訂單
  - available_cars.csv  各站每小時可用車輛數
  - map_browsing.csv    App 地圖點擊紀錄

站點來源：
  - data/orders_real.json  ← 台北市 YouBike 2.0 即時站點快照

使用方式:
    pip install pandas numpy
    python generate_fake_data.py
"""

import json
import pathlib
import random

import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

DATA_DIR = pathlib.Path(__file__).parent / "data"

# ── 參數設定 ─────────────────────────────────────────────────────────────────
N_ORDERS        = 20_000    # 訂單筆數
DATE_START      = "2023-01-01"
DATE_END        = "2025-05-31"
AVAIL_TOP_N     = 150       # available_cars / map_browsing 只取前 N 大站（控制檔案大小）
AVAIL_FREQ_DAYS = 7         # 供給資料取樣間隔（天）

# 24 小時借車機率（通勤 + 午休 + 傍晚高峰）
HOUR_PROBS = np.array([
    0.5, 0.3, 0.2, 0.1, 0.1, 0.3,   # 0–5
    0.8, 2.5, 3.5, 2.0, 1.5, 1.8,   # 6–11
    2.2, 1.8, 1.5, 1.6, 2.2, 3.8,   # 12–17
    3.5, 2.5, 1.8, 1.2, 0.9, 0.6,   # 18–23
])
HOUR_PROBS /= HOUR_PROBS.sum()
HOUR_PROB_MAX = HOUR_PROBS.max()

# 星期別加權（0=週一 … 6=週日）
DOW_WEIGHTS = np.array([1.2, 1.1, 1.0, 1.0, 1.3, 1.5, 1.4])
DOW_WEIGHTS /= DOW_WEIGHTS.sum()

BIKE_TYPES = ["YouBike 2.0 電輔版", "YouBike 1.0 一般版", "輕型電動車", "折疊單車"]
BIKE_WEIGHTS = np.array([0.50, 0.30, 0.12, 0.08])


# ════════════════════════════════════════════════════════════
# 0. 載入真實站點
# ════════════════════════════════════════════════════════════
print("載入真實站點資料 …")
with open(DATA_DIR / "orders_real.json", encoding="utf-8") as f:
    raw = json.load(f)

stations = pd.DataFrame(raw)
stations = stations[stations["act"].astype(str) == "1"].copy()
stations["Quantity"] = stations["Quantity"].astype(int)
stations["sno"] = stations["sno"].astype(str)   # 確保 ID 為字串

station_ids  = stations["sno"].tolist()
station_qty  = stations["Quantity"].values.astype(float)

# 站點熱度權重：依停車格數（越大 → 越熱門）
station_weights = station_qty / station_qty.sum()

print(f"  → 啟用站點：{len(stations)} 站")
print(f"  → 行政區分布：{dict(stations['sarea'].value_counts())}")


# ════════════════════════════════════════════════════════════
# 1. orders.csv
# ════════════════════════════════════════════════════════════
print(f"\n生成 orders.csv（{N_ORDERS:,} 筆）…")

all_dates = pd.date_range(DATE_START, DATE_END, freq="D")

order_rows = []
for oid in range(1, N_ORDERS + 1):
    # 選日期（依星期加權）
    dow_sample = np.random.choice(7, p=DOW_WEIGHTS)
    candidates = all_dates[all_dates.dayofweek == dow_sample]
    date = pd.Timestamp(np.random.choice(candidates))

    hour          = int(np.random.choice(24, p=HOUR_PROBS))
    booking_dt    = date + pd.Timedelta(hours=hour, minutes=random.randint(-30, 0))
    rent_start_dt = date + pd.Timedelta(hours=hour, minutes=random.randint(0, 15))

    # 租借時長：對數常態，中位約 30 分鐘
    duration_min = int(np.clip(np.random.lognormal(np.log(30), 0.7), 5, 480))
    rent_end_dt  = rent_start_dt + pd.Timedelta(minutes=duration_min)

    # 里程：與時長正相關
    speed_kmph   = random.uniform(10, 18)
    mileage_diff = round(max(0.5, duration_min / 60 * speed_kmph + random.gauss(0, 0.5)), 2)

    # 站點選擇（依容量加權）
    depart = np.random.choice(station_ids, p=station_weights)
    if random.random() < 0.65:
        return_lot = depart
    else:
        return_lot = np.random.choice(station_ids, p=station_weights)

    order_rows.append({
        "order_no":               f"ORD{oid:07d}",
        "booking_dt":             booking_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "rent_start_dt":          rent_start_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "rent_end_dt":            rent_end_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "acct_id":                f"U{random.randint(1, 8000):05d}",
        "depart_parking_lot_id":  depart,
        "return_parking_lot_id":  return_lot,
        "mileage_diff":           mileage_diff,
        "car_series_name":        np.random.choice(BIKE_TYPES, p=BIKE_WEIGHTS),
    })

orders_df = pd.DataFrame(order_rows)
orders_df.to_csv(DATA_DIR / "orders.csv", index=False)
print(f"  → {len(orders_df):,} 筆訂單寫入 orders.csv")


# ════════════════════════════════════════════════════════════
# 2. available_cars.csv
# ════════════════════════════════════════════════════════════
print(f"\n生成 available_cars.csv（前 {AVAIL_TOP_N} 大站，每 {AVAIL_FREQ_DAYS} 天取樣）…")

# 前 AVAIL_TOP_N 大站（依停車格數）作為供給資料來源
top_stations = (
    stations.nlargest(AVAIL_TOP_N, "Quantity")[["sno", "Quantity"]]
    .reset_index(drop=True)
)
sample_dates = pd.date_range(DATE_START, DATE_END, freq=f"{AVAIL_FREQ_DAYS}D")

avail_rows = []
for _, row in top_stations.iterrows():
    sid = row["sno"]
    qty = int(row["Quantity"])
    for d in sample_dates:
        for h in range(24):
            # 可用率：離峰高（~60%）、高峰低（~30%）
            avail_frac = 0.60 - 0.30 * (HOUR_PROBS[h] / HOUR_PROB_MAX)
            base = avail_frac * qty
            noise = np.random.poisson(lam=max(1, qty * 0.05))
            avail_cars = int(np.clip(base + random.gauss(0, noise), 0, qty))
            avail_rows.append({
                "available_date":  d.strftime("%Y-%m-%d"),
                "available_hour":  h,
                "parking_lot_id":  sid,
                "available_cars":  avail_cars,
            })

avail_df = pd.DataFrame(avail_rows)
avail_df.to_csv(DATA_DIR / "available_cars.csv", index=False)
print(f"  → {len(avail_df):,} 筆記錄寫入 available_cars.csv")


# ════════════════════════════════════════════════════════════
# 3. map_browsing.csv
# ════════════════════════════════════════════════════════════
print(f"\n生成 map_browsing.csv（前 {AVAIL_TOP_N} 大站，每 {AVAIL_FREQ_DAYS} 天取樣）…")

# 各站的 App 瀏覽基礎權重（與訂單熱度相同）
top_sno_list = top_stations["sno"].tolist()
top_qty      = top_stations["Quantity"].values.astype(float)
top_w        = top_qty / top_qty.sum()

browse_rows = []
for i, sid in enumerate(top_sno_list):
    for d in sample_dates:
        for h in range(24):
            # 瀏覽量 = 預估訂單量的 8–14 倍
            order_est = HOUR_PROBS[h] * N_ORDERS * top_w[i] * 3
            clicks    = int(max(1, np.random.poisson(lam=max(1, order_est * random.uniform(8, 14)))))
            browse_rows.append({
                "click_date":      d.strftime("%Y-%m-%d"),
                "click_hour":      h,
                "parking_lot_id":  sid,
                "num_click_times": clicks,
            })

browse_df = pd.DataFrame(browse_rows)
browse_df.to_csv(DATA_DIR / "map_browsing.csv", index=False)
print(f"  → {len(browse_df):,} 筆記錄寫入 map_browsing.csv")


print(f"\n✅ 完成！所有資料已寫入 {DATA_DIR.resolve()}")
print(f"   訂單站點 ID 格式：{order_rows[0]['depart_parking_lot_id']} …（真實 YouBike sno）")
print(f"   執行儀表板：streamlit run dashboard.py")
