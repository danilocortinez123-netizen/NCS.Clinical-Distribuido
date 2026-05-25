import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .agent import sync_agent
from .circuit_breaker import circuit_breaker
from .config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sync Agent - Local→Cloud Event Forwarder",
    description="Forwarder de eventos locales a cloud con circuit breaker y outbox pattern",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Iniciando Sync Agent...")
    asyncio.create_task(sync_agent.start())


@app.on_event("shutdown")
async def shutdown():
    logger.info("Deteniendo Sync Agent...")
    await sync_agent.stop()


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.service_name,
        "circuit_breaker": circuit_breaker.state,
        "cloud_connected": circuit_breaker.is_available and (sync_agent._cloud_conn is not None and not sync_agent._cloud_conn.is_closed) if sync_agent._cloud_conn else False,
    }


@app.get("/api/v1/admin/circuit-breaker")
async def circuit_breaker_status():
    return {
        "state": circuit_breaker.state,
        "failures": circuit_breaker._failures,
        "threshold": settings.circuit_breaker_threshold,
        "reset_seconds": settings.circuit_breaker_reset_seconds,
    }
