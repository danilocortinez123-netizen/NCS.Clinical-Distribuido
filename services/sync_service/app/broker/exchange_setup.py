import logging
from typing import Optional

import aio_pika
from aio_pika import ExchangeType

from .connection import broker_connection

logger = logging.getLogger(__name__)


EXCHANGE_CONFIG = {
    "patient.exchange": {
        "type": ExchangeType.TOPIC,
        "durable": True,
        "routing_keys": [
            "patient.created",
            "patient.updated",
            "patient.#",
        ],
    },
    "clinical.exchange": {
        "type": ExchangeType.TOPIC,
        "durable": True,
        "routing_keys": [
            "encounter.created",
            "observation.created",
            "condition.created",
            "clinical.#",
        ],
    },
    "sync.exchange": {
        "type": ExchangeType.TOPIC,
        "durable": True,
        "routing_keys": [
            "sync.patient.#",
            "sync.clinical.#",
            "sync.#",
        ],
    },
    "retry.exchange": {
        "type": ExchangeType.DIRECT,
        "durable": True,
        "routing_keys": [
            "patient.retry",
            "clinical.retry",
            "sync.retry",
        ],
    },
}

QUEUE_CONFIG = {
    # ─── Patient queues ─────────────────────────────────
    "patient.created.queue": {
        "exchange": "patient.exchange",
        "routing_key": "patient.created",
        "durable": True,
        "dlq": "patient.created.dlq",
        "retry_key": "patient.retry",
        "max_retries": 3,
    },
    "patient.updated.queue": {
        "exchange": "patient.exchange",
        "routing_key": "patient.updated",
        "durable": True,
        "dlq": "patient.updated.dlq",
        "retry_key": "patient.retry",
        "max_retries": 3,
    },
    "patient.all.queue": {
        "exchange": "patient.exchange",
        "routing_key": "patient.#",
        "durable": True,
        "dlq": "patient.all.dlq",
        "retry_key": "patient.retry",
        "max_retries": 3,
    },
    # ─── Clinical queues ────────────────────────────────
    "encounter.created.queue": {
        "exchange": "clinical.exchange",
        "routing_key": "encounter.created",
        "durable": True,
        "dlq": "encounter.created.dlq",
        "retry_key": "clinical.retry",
        "max_retries": 3,
    },
    "observation.created.queue": {
        "exchange": "clinical.exchange",
        "routing_key": "observation.created",
        "durable": True,
        "dlq": "observation.created.dlq",
        "retry_key": "clinical.retry",
        "max_retries": 3,
    },
    "condition.created.queue": {
        "exchange": "clinical.exchange",
        "routing_key": "condition.created",
        "durable": True,
        "dlq": "condition.created.dlq",
        "retry_key": "clinical.retry",
        "max_retries": 3,
    },
    "clinical.all.queue": {
        "exchange": "clinical.exchange",
        "routing_key": "clinical.#",
        "durable": True,
        "dlq": "clinical.all.dlq",
        "retry_key": "clinical.retry",
        "max_retries": 3,
    },
    # ─── Sync queues ────────────────────────────────────
    "sync.patient.queue": {
        "exchange": "sync.exchange",
        "routing_key": "sync.patient.#",
        "durable": True,
        "dlq": "sync.patient.dlq",
        "retry_key": "sync.retry",
        "max_retries": 3,
    },
    "sync.clinical.queue": {
        "exchange": "sync.exchange",
        "routing_key": "sync.clinical.#",
        "durable": True,
        "dlq": "sync.clinical.dlq",
        "retry_key": "sync.retry",
        "max_retries": 3,
    },
    "sync.all.queue": {
        "exchange": "sync.exchange",
        "routing_key": "sync.#",
        "durable": True,
        "dlq": "sync.all.dlq",
        "retry_key": "sync.retry",
        "max_retries": 3,
    },
    # ─── Retry queues (TTL-based) ───────────────────────
    "retry.patient.queue": {
        "exchange": "retry.exchange",
        "routing_key": "patient.retry",
        "durable": True,
        "ttl": 5000,
        "dlq": "patient.retry.dlq",
        "max_retries": 1,
    },
    "retry.clinical.queue": {
        "exchange": "retry.exchange",
        "routing_key": "clinical.retry",
        "durable": True,
        "ttl": 10000,
        "dlq": "clinical.retry.dlq",
        "max_retries": 1,
    },
    "retry.sync.queue": {
        "exchange": "retry.exchange",
        "routing_key": "sync.retry",
        "durable": True,
        "ttl": 30000,
        "dlq": "sync.retry.dlq",
        "max_retries": 1,
    },
    # ─── Dead letter queues ─────────────────────────────
    "patient.created.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "patient.updated.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "patient.all.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "patient.retry.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "encounter.created.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "observation.created.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "condition.created.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "clinical.all.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "clinical.retry.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "sync.patient.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "sync.clinical.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "sync.all.dlq": {"exchange": None, "routing_key": None, "durable": True},
    "sync.retry.dlq": {"exchange": None, "routing_key": None, "durable": True},
}

RETRY_TTL_SECONDS = [5, 30, 120]


class ExchangeSetup:
    """Declara toda la topología de exchanges, colas y bindings."""

    def __init__(self):
        self._exchanges: dict[str, aio_pika.Exchange] = {}

    async def declare_all(
        self, channel: aio_pika.RobustChannel
    ) -> dict[str, aio_pika.Exchange]:
        exchanges = await self._declare_exchanges(channel)
        self._exchanges = exchanges
        await self._declare_queues(channel)
        await self._declare_bindings(channel)
        logger.info("Topología RabbitMQ declarada exitosamente")
        return exchanges

    async def _declare_exchanges(
        self, channel: aio_pika.RobustChannel
    ) -> dict[str, aio_pika.Exchange]:
        exchanges = {}
        for name, config in EXCHANGE_CONFIG.items():
            exchange = await channel.declare_exchange(
                name=name,
                type=config["type"],
                durable=config["durable"],
            )
            exchanges[name] = exchange
            logger.debug(f"Exchange declarado: {name} ({config['type'].value})")
        return exchanges

    async def _declare_queues(self, channel: aio_pika.RobustChannel):
        for name, config in QUEUE_CONFIG.items():
            arguments = {}
            dlq = config.get("dlq")
            if dlq:
                arguments["x-dead-letter-exchange"] = ""
                arguments["x-dead-letter-routing-key"] = dlq

            ttl = config.get("ttl")
            if ttl:
                arguments["x-message-ttl"] = ttl

            await channel.declare_queue(
                name=name,
                durable=config["durable"],
                arguments=arguments,
            )
            logger.debug(f"Cola declarada: {name}")

    async def _declare_bindings(self, channel: aio_pika.RobustChannel):
        for name, config in QUEUE_CONFIG.items():
            exchange_name = config.get("exchange")
            routing_key = config.get("routing_key")
            if exchange_name and routing_key:
                exchange = self._exchanges.get(exchange_name)
                if exchange:
                    queue = await channel.get_queue(name)
                    await queue.bind(exchange=exchange, routing_key=routing_key)
                    logger.debug(f"Binding: {name} → {exchange_name}[{routing_key}]")

    def get_exchange(self, name: str) -> Optional[aio_pika.Exchange]:
        return self._exchanges.get(name)


exchange_setup = ExchangeSetup()
