import asyncio
import logging
from typing import Optional

import aio_pika

from ..config import settings

logger = logging.getLogger(__name__)


class RabbitMQConnection:
    """Gestor de conexión RabbitMQ con reconexión automática."""

    def __init__(self):
        self._connection: Optional[aio_pika.RobustConnection] = None
        self._channel: Optional[aio_pika.RobustChannel] = None
        self._max_retries = 30
        self._retry_delay = 3.0

    async def connect(self) -> aio_pika.RobustConnection:
        if self._connection and not self._connection.is_closed:
            return self._connection

        for attempt in range(1, self._max_retries + 1):
            try:
                self._connection = await aio_pika.connect_robust(
                    host=settings.rabbitmq_host,
                    port=settings.rabbitmq_port,
                    login=settings.rabbitmq_user,
                    password=settings.rabbitmq_password,
                    virtualhost=settings.rabbitmq_vhost,
                    heartbeat=60,
                )
                logger.info(f"RabbitMQ conectado (intento {attempt})")
                return self._connection
            except Exception as e:
                logger.warning(
                    f"Fallo conexión RabbitMQ (intento {attempt}/{self._max_retries}): {e}"
                )
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_delay * attempt)

        raise ConnectionError(
            f"No se pudo conectar a RabbitMQ tras {self._max_retries} intentos"
        )

    async def get_channel(self) -> aio_pika.RobustChannel:
        conn = await self.connect()
        if self._channel and not self._channel.is_closed:
            return self._channel
        self._channel = await conn.channel()
        await self._channel.set_qos(prefetch_count=10)
        return self._channel

    async def close(self):
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()
        logger.info("Conexión RabbitMQ cerrada")


broker_connection = RabbitMQConnection()
