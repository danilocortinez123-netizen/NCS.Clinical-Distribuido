FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/gateway_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/gateway_service/ ./services/gateway_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "services.gateway_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
