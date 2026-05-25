import json
import logging
from typing import Any, Optional

import aio_pika
from aio_pika import DeliveryMode, Message

logger = logging.getLogger(__name__)


class BasePublisher:
    """Publisher base con confirmaciones y correlación."""

    def __init__(self, exchange: aio_pika.Exchange):
        self._exchange = exchange

    async def publish(
        self,
        routing_key: str,
        event_id: str,
        event_type: str,
        source: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
        retry_count: int = 0,
        headers: Optional[dict[str, str]] = None,
    ):
        body = {
            "event_id": event_id,
            "event_type": event_type,
            "source": source,
            "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
            "correlation_id": correlation_id,
            "data": data,
            "retry_count": retry_count,
        }

        message_headers = headers or {}
        message_headers.update({
            "x-event-id": event_id,
            "x-event-type": event_type,
            "x-source": source,
        })
        if correlation_id:
            message_headers["x-correlation-id"] = correlation_id

        message = Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
            message_id=event_id,
            type=event_type,
            correlation_id=correlation_id or event_id,
            headers=message_headers,
        )

        try:
            confirm = await self._exchange.publish(
                message=message,
                routing_key=routing_key,
                mandatory=True,
                timeout=30.0,
            )
            if confirm:
                logger.debug(
                    f"Evento publicado: {event_type}[{event_id}] → {routing_key}"
                )
            return True
        except aio_pika.exceptions.DeliveryError as e:
            logger.error(
                f"Error de entrega {event_type}[{event_id}]: {e}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Error publicando {event_type}[{event_id}]: {e}"
            )
            raise
