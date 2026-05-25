import json
import logging
from typing import Any, Callable, Optional

import aio_pika
from aio_pika import ExchangeType

from ..broker.connection import broker_connection
from ..broker.exchange_setup import exchange_setup, RETRY_TTL_SECONDS
from ..persistence.idempotency import idempotency_store

logger = logging.getLogger(__name__)


class BaseConsumer:
    """Consumer base con:
    - Idempotencia (evita procesar el mismo evento dos veces)
    - Retry con backoff progresivo (5s → 30s → 120s → DLQ)
    - Dead Letter Queue (DLQ) tras agotar retries
    - Manejo graceful de errores
    """

    def __init__(
        self,
        queue_name: str,
        handler: Callable,
        max_retries: int = 3,
        prefetch_count: int = 10,
    ):
        self.queue_name = queue_name
        self.handler = handler
        self.max_retries = max_retries
        self.prefetch_count = prefetch_count
        self._channel: Optional[aio_pika.RobustChannel] = None

    async def start(self):
        channel = await broker_connection.get_channel()
        await channel.set_qos(prefetch_count=self.prefetch_count)

        queue = await channel.get_queue(self.queue_name)
        self._channel = channel

        logger.info(f"Consumer iniciado: {self.queue_name}")
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process(ignore_processed=True):
                    await self._process_with_retry(message)

    async def _process_with_retry(self, message: aio_pika.IncomingMessage):
        try:
            body = json.loads(message.body.decode())
        except json.JSONDecodeError as e:
            logger.error(f"JSON inválido en {self.queue_name}: {e}")
            await message.reject(requeue=False)
            return

        event_id = body.get("event_id") or message.message_id
        event_type = body.get("event_type", message.type)
        retry_count = body.get("retry_count", 0)

        if event_id and idempotency_store.is_processed(event_id):
            logger.info(f"Evento duplicado ignorado: {event_id}")
            await message.ack()
            return

        try:
            logger.info(f"Procesando evento: {event_type}[{event_id}] en {self.queue_name}")
            result = await self.handler(body)
            if event_id:
                idempotency_store.mark_processed(event_id, event_type)
            await message.ack()
            logger.info(f"Evento procesado exitosamente: {event_type}[{event_id}]")
            return result

        except Exception as e:
            logger.error(f"Error procesando {event_type}[{event_id}]: {e}", exc_info=True)

            if retry_count < self.max_retries:
                await self._publish_retry(body, retry_count)
                await message.ack()
                logger.info(
                    f"Reintentando {event_type}[{event_id}] "
                    f"(intento {retry_count + 1}/{self.max_retries})"
                )
            else:
                await self._send_to_dlq(body, str(e))
                await message.ack()
                logger.warning(
                    f"Evento enviado a DLQ tras {self.max_retries} intentos: "
                    f"{event_type}[{event_id}]"
                )

    async def _publish_retry(self, body: dict, current_retry: int):
        channel = await broker_connection.get_channel()
        retry_exchange = await channel.declare_exchange(
            name="retry.exchange",
            type=ExchangeType.DIRECT,
            durable=True,
        )

        body["retry_count"] = current_retry + 1

        retry_message = aio_pika.Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            headers={"x-retry-count": str(current_retry + 1)},
        )

        routing_key = self.queue_name.replace(".queue", ".retry")
        domain = routing_key.split(".")[0]
        retry_routing = f"{domain}.retry"

        await retry_exchange.publish(
            message=retry_message,
            routing_key=retry_routing,
            mandatory=True,
        )

    async def _send_to_dlq(self, body: dict, error: str):
        channel = await broker_connection.get_channel()
        dlq_name = self.queue_name.replace(".queue", ".dlq")

        body["error"] = error
        body["final_attempt"] = True

        dlq_message = aio_pika.Message(
            body=json.dumps(body).encode(),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )

        await channel.default_exchange.publish(
            message=dlq_message,
            routing_key=dlq_name,
        )

        if body.get("event_id"):
            idempotency_store.mark_failed(body["event_id"], body.get("event_type", "unknown"))

    async def close(self):
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
