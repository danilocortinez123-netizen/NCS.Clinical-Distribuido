FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY services/patient_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/patient_service/ ./services/patient_service/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["uvicorn", "services.patient_service.app.main:app", "--host", "0.0.0.0", "--port", "8002"]
