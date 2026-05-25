import json
import logging
from typing import Any, Optional

import aio_pika
import psycopg2
from aio_pika import DeliveryMode, Message

from ..config import settings

logger = logging.getLogger(__name__)


class EventDispatcher:
    def __init__(self):
        self._connection = None
        self._exchange = None
        self._db_conn = None

    def _get_outbox_db(self):
        if self._db_conn is None or self._db_conn.closed:
            self._db_conn = psycopg2.connect(
                host=settings.events_db_host,
                port=settings.events_db_port,
                user=settings.events_db_user,
                password=settings.events_db_password,
                dbname=settings.events_db_name,
            )
        return self._db_conn

    def _write_outbox(self, event_id: str, event_type: str, source: str, data: dict, correlation_id: Optional[str] = None):
        try:
            conn = self._get_outbox_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO event_outbox (event_id, event_type, source, correlation_id, data)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event_id, event_type, source, correlation_id or "", json.dumps(data)),
                )
                conn.commit()
        except Exception as e:
            logger.warning("Outbox write falló (no crítico): %s", e)

    async def _ensure_connected(self):
        if self._exchange is not None:
            return
        self._connection = await aio_pika.connect_robust(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            login=settings.rabbitmq_user,
            password=settings.rabbitmq_password,
        )
        channel = await self._connection.channel()
        self._exchange = await channel.declare_exchange(
            name=settings.events_exchange,
            type=aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    def _build_body(self, event_id: str, event_type: str, entity_id: str, data: dict[str, Any], correlation_id: Optional[str] = None) -> dict:
        key = f"{event_type.split('.')[0]}_id"
        return {
            "event_id": event_id,
            "event_type": event_type,
            "source": settings.service_name,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "correlation_id": correlation_id or entity_id,
            "data": {key: entity_id, **data},
            "retry_count": 0,
        }

    async def _publish(self, body: dict, event_type: str, routing_key: str, entity_id: str, correlation_id: Optional[str] = None):
        message = Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=body["event_id"],
            type=event_type,
            correlation_id=correlation_id or entity_id,
        )
        await self._exchange.publish(message=message, routing_key=routing_key)
        logger.info(f"Evento publicado: {event_type}[{entity_id}]")

    async def publish_encounter_created(self, encounter_id: int, data: dict[str, Any], correlation_id: Optional[str] = None):
        await self._ensure_connected()
        event_id = f"encounter.created.{encounter_id}"
        body = self._build_body(event_id, "encounter.created", str(encounter_id), data, correlation_id)
        self._write_outbox(event_id, "encounter.created", settings.service_name, body, correlation_id)
        await self._publish(body, "encounter.created", "encounter.created", str(encounter_id), correlation_id)

    async def publish_observation_created(self, observation_id: str, data: dict[str, Any], correlation_id: Optional[str] = None):
        await self._ensure_connected()
        event_id = f"observation.created.{observation_id}"
        body = self._build_body(event_id, "observation.created", observation_id, data, correlation_id)
        self._write_outbox(event_id, "observation.created", settings.service_name, body, correlation_id)
        await self._publish(body, "observation.created", "observation.created", observation_id, correlation_id)

    async def publish_condition_created(self, condition_id: int, data: dict[str, Any], correlation_id: Optional[str] = None):
        await self._ensure_connected()
        event_id = f"condition.created.{condition_id}"
        body = self._build_body(event_id, "condition.created", str(condition_id), data, correlation_id)
        self._write_outbox(event_id, "condition.created", settings.service_name, body, correlation_id)
        await self._publish(body, "condition.created", "condition.created", str(condition_id), correlation_id)

    async def close(self):
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        if self._db_conn and not self._db_conn.closed:
            self._db_conn.close()


event_dispatcher = EventDispatcher()
