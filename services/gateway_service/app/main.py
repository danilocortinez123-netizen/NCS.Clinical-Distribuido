from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .middleware.jwt_auth import JWTAuthMiddleware
from .routes import proxy, frontend, real_backend

app = FastAPI(
    title="Historia Clínica Distribuida - API Gateway",
    description="API Gateway con autenticación JWT y enrutamiento a microservicios",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(JWTAuthMiddleware)

from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_client import Gauge
import asyncio
import time
from .routes.real_backend import get_db_conn

app.include_router(frontend.router)
app.include_router(proxy.router)
app.include_router(real_backend.router)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# --- Custom Metrics ---
his_outbox_pending_total = Gauge("his_outbox_pending_total", "Total de eventos en pending")
his_outbox_processed_total = Gauge("his_outbox_processed_total", "Total de eventos procesados")
his_outbox_failed_total = Gauge("his_outbox_failed_total", "Total de eventos fallidos")
his_outbox_pending_by_node = Gauge("his_outbox_pending_by_node", "Pendientes por nodo", ["node"])
his_outbox_failed_by_node = Gauge("his_outbox_failed_by_node", "Fallidos por nodo", ["node"])
his_outbox_last_sync_timestamp = Gauge("his_outbox_last_sync_timestamp", "Timestamp de la última sincronización")

async def update_outbox_metrics():
    while True:
        try:
            conn = get_db_conn()
            with conn.cursor() as cur:
                # Totales
                cur.execute("SELECT LOWER(status), COUNT(*) FROM event_outbox GROUP BY LOWER(status)")
                counts = {"pending": 0, "processed": 0, "failed": 0}
                for row in cur.fetchall():
                    if row[0] in counts:
                        counts[row[0]] = row[1]
                
                his_outbox_pending_total.set(counts["pending"])
                his_outbox_processed_total.set(counts["processed"])
                his_outbox_failed_total.set(counts["failed"])
                
                # Por nodo (pending)
                cur.execute("SELECT COALESCE(data->>'sede', data->>'sede_origen', data->>'source_node', source), COUNT(*) FROM event_outbox WHERE LOWER(status)='pending' GROUP BY 1")
                nodes_pending = {row[0]: row[1] for row in cur.fetchall()}
                for node in ["Sincelejo", "Bogotá", "Medellín"]:
                    his_outbox_pending_by_node.labels(node=node).set(nodes_pending.get(node, nodes_pending.get(node.lower(), 0)))
                
                # Por nodo (failed)
                cur.execute("SELECT COALESCE(data->>'sede', data->>'sede_origen', data->>'source_node', source), COUNT(*) FROM event_outbox WHERE LOWER(status)='failed' GROUP BY 1")
                nodes_failed = {row[0]: row[1] for row in cur.fetchall()}
                for node in ["Sincelejo", "Bogotá", "Medellín"]:
                    his_outbox_failed_by_node.labels(node=node).set(nodes_failed.get(node, nodes_failed.get(node.lower(), 0)))
                
                # Ultimo sync
                cur.execute("SELECT MAX(published_at) FROM event_outbox WHERE LOWER(status)='processed'")
                last_sync = cur.fetchone()[0]
                if last_sync:
                    his_outbox_last_sync_timestamp.set(last_sync.timestamp())
            conn.close()
        except Exception as e:
            print(f"Error updating metrics: {e}")
        await asyncio.sleep(10)

@app.on_event("startup")
async def start_metrics_task():
    asyncio.create_task(update_outbox_metrics())


try:
    app.mount(
        "/static",
        StaticFiles(directory="/app/frontend/static"),
        name="static",
    )
except RuntimeError:
    pass


@app.get("/")
async def root():
    return {
        "service": settings.service_name,
        "version": "3.0.0",
        "endpoints": {
            "patient": "/api/v1/patient",
            "clinical": "/api/v1/clinical",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.service_name}
