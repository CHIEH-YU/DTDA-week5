FROM python:3.11-slim

WORKDIR /app

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式
COPY dashboard_bigquery.py .

# Cloud Run 透過 PORT 環境變數指定 port（預設 8080）
ENV PORT=8080

EXPOSE ${PORT}

# 使用 sh -c 讓 ${PORT} 在執行時展開
CMD ["sh", "-c", \
     "python -m streamlit run dashboard_bigquery.py \
     --server.port=${PORT} \
     --server.address=0.0.0.0 \
     --server.headless=true \
     --server.enableCORS=false \
     --server.enableXsrfProtection=false"]
