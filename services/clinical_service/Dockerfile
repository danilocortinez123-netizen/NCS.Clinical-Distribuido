FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY services/clinical_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/clinical_service/ ./services/clinical_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8003

CMD ["uvicorn", "services.clinical_service.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
