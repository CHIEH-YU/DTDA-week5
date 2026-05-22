FROM python:3.11-slim

WORKDIR /app

COPY cloudrun/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY cloudrun/dashboard.py .
COPY data/ ./data/

# Cloud Run 透過 PORT 環境變數指定 port（預設 8080）
ENV PORT=8080

EXPOSE ${PORT}

CMD ["sh", "-c", \
     "python -m streamlit run dashboard.py \
     --server.port=${PORT} \
     --server.address=0.0.0.0 \
     --server.headless=true \
     --server.enableCORS=false \
     --server.enableXsrfProtection=false"]
