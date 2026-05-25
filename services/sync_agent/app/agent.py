import asyncio
import json
import logging
from typing import Optional

import aio_pika
import psycopg2
from aio_pika import DeliveryMode, ExchangeType, Message

from .circuit_breaker import circuit_breaker
from .config import settings

logger = logging.getLogger(__name__)

LOCAL_QUEUES = [
    "patient.created.queue",
    "patient.updated.queue",
    "patient.all.queue",
    "encounter.created.queue",
    "observation.created.queue",
    "condition.created.queue",
    "clinical.all.queue",
]

QUEUE_TO_CLOUD = {
    "patient.created.queue": ("patient.exchange", "patient.created"),
    "patient.updated.queue": ("patient.exchange", "patient.updated"),
    "patient.all.queue": ("patient.exchange", "patient.#"),
    "encounter.created.queue": ("clinical.exchange", "encounter.created"),
    "observation.created.queue": ("clinical.exchange", "observation.created"),
    "condition.created.queue": ("clinical.exchange", "condition.created"),
    "clinical.all.queue": ("clinical.exchange", "clinical.#"),
}


class SyncAgent:
    def __init__(self):
        self._local_conn: Optional[aio_pika.RobustConnection] = None
        self._cloud_conn: Optional[aio_pika.RobustConnection] = None
        self._db_conn: Optional[psycopg2.extensions.connection] = None
        self._consumers: list[asyncio.Task] = []
        self._running = False
        self._poller_task: Optional[asyncio.Task] = None

    def _get_db(self):
        if self._db_conn is None or self._db_conn.closed:
            self._db_conn = psycopg2.connect(
                host=settings.events_db_host,
                port=settings.events_db_port,
                user=settings.events_db_user,
                password=settings.events_db_password,
                dbname=settings.events_db_name,
            )
            self._init_outbox_table()
        return self._db_conn

    def _init_outbox_table(self):
        with self._db_conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS sync_agent_outbox (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(128) NOT NULL UNIQUE,
                    original_body JSONB NOT NULL,
                    cloud_exchange VARCHAR(64) NOT NULL,
                    cloud_routing_key VARCHAR(64) NOT NULL,
                    status VARCHAR(16) DEFAULT 'pending',
                    retry_count INT DEFAULT 0,
                    last_error TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    published_at TIMESTAMP
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_outbox_status
                ON sync_agent_outbox (status, created_at)
            """)
        self._db_conn.commit()

    def _write_outbox(self, event_id: str, body: dict, exchange: str, routing_key: str):
        try:
            conn = self._get_db()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO sync_agent_outbox (event_id, original_body, cloud_exchange, cloud_routing_key)
                    VALUES (%s, %s::jsonb, %s, %s)
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event_id, json.dumps(body), exchange, routing_key),
                )
                conn.commit()
        except Exception as e:
            logger.error("Outbox write error: %s", e)

    def _fetch_pending_outbox(self, limit: int = 50):
        conn = self._get_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, event_id, original_body, cloud_exchange, cloud_routing_key, retry_count
                FROM sync_agent_outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (limit,),
            )
            return [dict(r) for r in cur.fetchall()]

    def _mark_outbox_published(self, record_id: int):
        conn = self._get_db()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sync_agent_outbox SET status = 'published', published_at = NOW() WHERE id = %s",
                (record_id,),
            )
            conn.commit()

    def _mark_outbox_failed(self, record_id: int, error: str):
        conn = self._get_db()
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE sync_agent_outbox SET status = 'failed', retry_count = retry_count + 1, last_error = %s WHERE id = %s",
                (error, record_id),
            )
            conn.commit()

    async def _connect_local(self):
        self._local_conn = await aio_pika.connect_robust(
            host=settings.local_rabbitmq_host,
            port=settings.local_rabbitmq_port,
            login=settings.local_rabbitmq_user,
            password=settings.local_rabbitmq_password,
        )
        logger.info("Conectado a RabbitMQ local: %s:%s", settings.local_rabbitmq_host, settings.local_rabbitmq_port)

    async def _get_cloud_connection(self):
        if self._cloud_conn is None or self._cloud_conn.is_closed:
            if not circuit_breaker.is_available:
                raise ConnectionError(f"Circuit breaker {circuit_breaker.state}, saltando forward a cloud")
            try:
                self._cloud_conn = await aio_pika.connect_robust(
                    host=settings.cloud_rabbitmq_host,
                    port=settings.cloud_rabbitmq_port,
                    login=settings.cloud_rabbitmq_user,
                    password=settings.cloud_rabbitmq_password,
                    timeout=5,
                )
                circuit_breaker.record_success()
                logger.info("Conectado a RabbitMQ cloud: %s:%s", settings.cloud_rabbitmq_host, settings.cloud_rabbitmq_port)
                return self._cloud_conn
            except Exception as e:
                circuit_breaker.record_failure()
                logger.warning("Cloud RabbitMQ no disponible: %s (circuit=%s)", e, circuit_breaker.state)
                raise
        return self._cloud_conn

    async def _forward_to_cloud(self, body: dict, exchange_name: str, routing_key: str):
        conn = await self._get_cloud_connection()
        channel = await conn.channel()
        try:
            exchange = await channel.declare_exchange(
                name=exchange_name,
                type=ExchangeType.TOPIC,
                durable=True,
            )
            msg = Message(
                body=json.dumps(body).encode(),
                content_type="application/json",
                delivery_mode=DeliveryMode.PERSISTENT,
                message_id=body.get("event_id", ""),
                type=body.get("event_type", ""),
                correlation_id=body.get("correlation_id", ""),
            )
            await exchange.publish(msg, routing_key=routing_key, mandatory=True)
            logger.info("Forwarded %s → cloud[%s/%s]", body.get("event_type"), exchange_name, routing_key)
        finally:
            await channel.close()

    async def _process_local_event(self, message: aio_pika.IncomingMessage):
        async with message.process(ignore_processed=True):
            body = json.loads(message.body.decode())

            routing_key = message.routing_key or ""
            event_id = body.get("event_id", "")

            queue_name = getattr(message, "queue_name", "")
            cloud_info = QUEUE_TO_CLOUD.get(queue_name)
            if not cloud_info:
                logger.warning("No cloud mapping for queue: %s", queue_name)
                return

            cloud_exchange, cloud_routing = cloud_info
            logger.info("Procesando %s para forward a cloud", event_id)

            try:
                await self._forward_to_cloud(body, cloud_exchange, cloud_routing)
            except Exception as e:
                logger.warning("Forward falló, guardando en outbox: %s - %s", event_id, e)
                self._write_outbox(event_id, body, cloud_exchange, cloud_routing)

    async def _run_consumer(self, queue_name: str):
        channel = await self._local_conn.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.get_queue(queue_name)
        logger.info("Consumer sync-agent iniciado: %s", queue_name)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if not self._running:
                    break
                await self._process_local_event(message)

    async def _retry_outbox(self):
        pending = self._fetch_pending_outbox()
        if not pending:
            return

        logger.info("Outbox retry: %d eventos pendientes", len(pending))
        for record in pending:
            try:
                body = record["original_body"] if isinstance(record["original_body"], dict) else json.loads(record["original_body"])
                await self._forward_to_cloud(body, record["cloud_exchange"], record["cloud_routing_key"])
                self._mark_outbox_published(record["id"])
                logger.info("Outbox published: %s", record["event_id"])
            except Exception as e:
                logger.warning("Outbox retry falló para %s: %s", record["event_id"], e)
                self._mark_outbox_failed(record["id"], str(e))

    async def _poller_loop(self):
        while self._running:
            try:
                if circuit_breaker.is_available:
                    await self._retry_outbox()
            except Exception as e:
                logger.debug("Poller cycle error: %s", e)
            await asyncio.sleep(settings.poll_interval)

    async def start(self):
        self._running = True

        await self._connect_local()

        for qname in LOCAL_QUEUES:
            task = asyncio.create_task(self._run_consumer(qname))
            self._consumers.append(task)

        self._poller_task = asyncio.create_task(self._poller_loop())

        logger.info("Sync-agent iniciado: %d consumers + outbox retry cada %ds", len(LOCAL_QUEUES), settings.poll_interval)

    async def stop(self):
        self._running = False
        for t in self._consumers:
            t.cancel()
        if self._poller_task:
            self._poller_task.cancel()
        await asyncio.gather(*self._consumers, return_exceptions=True)
        if self._local_conn and not self._local_conn.is_closed:
            await self._local_conn.close()
        if self._cloud_conn and not self._cloud_conn.is_closed:
            await self._cloud_conn.close()
        if self._db_conn and not self._db_conn.closed:
            self._db_conn.close()
        logger.info("Sync-agent detenido")


sync_agent = SyncAgent()
