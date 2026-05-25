import asyncio
import json
import logging
from typing import Optional

import aio_pika
from aio_pika import DeliveryMode, Message

from .outbox import outbox_store
from ..broker.connection import broker_connection
from ..config import settings

logger = logging.getLogger(__name__)

EVENT_ROUTING: dict[str, tuple[str, str]] = {
    "patient.created": ("patient.exchange", "patient.created"),
    "PatientCreated": ("patient.exchange", "patient.created"),
    "patient.updated": ("patient.exchange", "patient.updated"),
    "PatientUpdated": ("patient.exchange", "patient.updated"),
    "patient.imported": ("patient.exchange", "patient.updated"),
    "encounter.created": ("clinical.exchange", "encounter.created"),
    "observation.created": ("clinical.exchange", "observation.created"),
    "condition.created": ("clinical.exchange", "condition.created"),
    "clinical.created": ("clinical.exchange", "clinical.all"),
    "clinical_record.created": ("clinical.exchange", "clinical.all"),
    "ClinicalRecordCreated": ("clinical.exchange", "clinical.all"),
}

POLL_INTERVAL_SECONDS = 5
BATCH_SIZE = 50


class OutboxPoller:
    """Background poller: lee event_outbox y publica eventos pendientes."""

    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._run())
        logger.info("Outbox poller iniciado (intervalo=%ss)", POLL_INTERVAL_SECONDS)

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Outbox poller detenido")

    async def _run(self):
        while self._running:
            try:
                await self._poll_once()
            except Exception:
                logger.exception("Error en ciclo de outbox poller")
            await asyncio.sleep(POLL_INTERVAL_SECONDS)

    async def _poll_once(self):
        logger.info("Outbox poller tick")
        pending = outbox_store.fetch_pending(BATCH_SIZE)
        if not pending:
            return

        logger.info(f"Eventos pendientes encontrados: {len(pending)}")
        conn = await broker_connection.connect()
        channel = await conn.channel()

        try:
            for record in pending:
                await self._publish_one(channel, record)
        finally:
            await channel.close()

    async def _publish_one(self, channel: aio_pika.RobustChannel, record: dict):
        event_type = record["event_type"]
        event_id = record["event_id"]
        record_id = record["id"]
        
        logger.info(f"Procesando evento {event_id}")
        outbox_store.mark_processing(record_id)
        
        routing_config = EVENT_ROUTING.get(event_type)
        if not routing_config:
            logger.warning("Tipo de evento desconocido en outbox: %s", event_type)
            outbox_store.mark_failed(record_id, f"Unknown event_type: {event_type}")
            return

        exchange_name, routing_key = routing_config
        body = record["data"] if isinstance(record["data"], dict) else json.loads(record["data"])
        body.setdefault("event_id", event_id)
        body.setdefault("event_type", event_type)
        body.setdefault("source", record["source"])
        body.setdefault("correlation_id", record.get("correlation_id"))

        exchange = await channel.declare_exchange(
            name=exchange_name,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

        message = Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=event_id,
            type=event_type,
            correlation_id=record.get("correlation_id") or "",
        )

        try:
            # Publicar en RabbitMQ
            await exchange.publish(
                message=message,
                routing_key=routing_key,
                mandatory=True,
            )
            logger.info("Publicado en RabbitMQ")

            # Consumir/procesar hacia HAPI FHIR llamando directamente al handler
            from ..handlers.patient_handler import patient_handler
            from ..handlers.clinical_handler import clinical_handler

            logger.info("Enviando Patient a HAPI FHIR")
            
            if event_type in ("patient.created", "PatientCreated"):
                result = await patient_handler.handle_created({"event_id": event_id, "data": body})
                logger.info(f"FHIR response status: {result.get('status', 'ok')}")
                outbox_store.mark_patient_synced(body.get("patient_id"))
                logger.info("Paciente marcado como SYNCED")
            elif event_type in ("patient.updated", "PatientUpdated"):
                result = await patient_handler.handle_updated({"event_id": event_id, "data": body})
            elif event_type in ("clinical.created", "clinical_record.created", "ClinicalRecordCreated"):
                result = await clinical_handler.handle_sync({"event_id": event_id, "data": body})
                
            outbox_store.mark_published(record_id)
            logger.info("Evento marcado como processed")
            
        except Exception as e:
            logger.error("Outbox falló: %s[%s]: %s", event_type, event_id, e)
            outbox_store.mark_failed(record_id, str(e))

outbox_poller = OutboxPoller()
