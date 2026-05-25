FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/sync_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/sync_service/ ./services/sync_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8004

CMD ["uvicorn", "services.sync_service.app.main:app", "--host", "0.0.0.0", "--port", "8004"]
