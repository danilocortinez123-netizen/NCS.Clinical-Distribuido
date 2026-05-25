FROM python:3.11-slim

WORKDIR /app

COPY services/sync_agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/sync_agent/ ./services/sync_agent/
COPY shared/ ./shared/

ENV PYTHONPATH=/app

EXPOSE 8005

CMD ["uvicorn", "services.sync_agent.app.main:app", "--host", "0.0.0.0", "--port", "8005"]
