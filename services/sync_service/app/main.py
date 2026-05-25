import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .broker.connection import broker_connection
from .broker.exchange_setup import exchange_setup
from .consumers.patient_consumer import (
    patient_created_consumer,
    patient_updated_consumer,
    patient_all_consumer,
)
from .consumers.clinical_consumer import (
    encounter_consumer,
    observation_consumer,
    condition_consumer,
    clinical_all_consumer,
)
from .consumers.sync_consumer import (
    sync_patient_consumer,
    sync_clinical_consumer,
    sync_all_consumer,
)
from .persistence.idempotency import idempotency_store
from .persistence.outbox import outbox_store
from .persistence.outbox_poller import outbox_poller
from .api.admin_routes import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sync Service - Event Bus Enterprise",
    description="Sistema de eventos asíncronos con RabbitMQ para HC distribuida",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from prometheus_fastapi_instrumentator import Instrumentator

app.include_router(admin_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

consumer_tasks: list[asyncio.Task] = []
consumer_instances = [
    patient_created_consumer,
    patient_updated_consumer,
    patient_all_consumer,
    encounter_consumer,
    observation_consumer,
    condition_consumer,
    clinical_all_consumer,
    sync_patient_consumer,
    sync_clinical_consumer,
    sync_all_consumer,
]


@app.on_event("startup")
async def startup():
    logger.info("Iniciando Sync Service con topología enterprise...")

    conn = await broker_connection.connect()
    channel = await conn.channel()
    await exchange_setup.declare_all(channel)
    await channel.close()

    for consumer in consumer_instances:
        task = asyncio.create_task(consumer.start())
        consumer_tasks.append(task)

    if settings.auto_sync_enabled:
        await outbox_poller.start()
        logger.info(f"Sync Service iniciado con {len(consumer_instances)} consumers + outbox poller")
    else:
        logger.info("AUTO_SYNC desactivado: Outbox solo se procesará manualmente")
        logger.info(f"Sync Service iniciado con {len(consumer_instances)} consumers")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Deteniendo Sync Service...")
    await outbox_poller.stop()
    for task in consumer_tasks:
        task.cancel()
    await asyncio.gather(*consumer_tasks, return_exceptions=True)
    idempotency_store.close()
    await broker_connection.close()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "consumers": len(consumer_instances),
        "consumers_running": sum(1 for t in consumer_tasks if not t.done()),
    }
