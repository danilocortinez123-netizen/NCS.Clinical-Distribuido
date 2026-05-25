import json
import logging
from datetime import datetime
from typing import Any, Optional

import psycopg2
import psycopg2.extras

from ..config import settings

logger = logging.getLogger(__name__)


class OutboxStore:
    """Outbox pattern: almacena eventos para publicación garantizada.
    
    Los servicios escriben eventos en esta tabla dentro de su transacción local.
    Un proceso separado (poller) lee y publica en RabbitMQ, marcando como enviados.
    """

    def __init__(self):
        self._conn = None

    def _get_conn(self):
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=settings.events_db_host,
                port=settings.events_db_port,
                user=settings.events_db_user,
                password=settings.events_db_password,
                dbname=settings.events_db_name,
            )
            self._init_table()
        return self._conn

    def _init_table(self):
        with self._conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS event_outbox (
                    id SERIAL PRIMARY KEY,
                    event_id VARCHAR(64) NOT NULL UNIQUE,
                    event_type VARCHAR(64) NOT NULL,
                    source VARCHAR(64) NOT NULL,
                    correlation_id VARCHAR(64),
                    data JSONB NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'pending',
                    retry_count INT DEFAULT 0,
                    created_at TIMESTAMP DEFAULT NOW(),
                    published_at TIMESTAMP,
                    last_error TEXT
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_outbox_status
                ON event_outbox (status, created_at)
            """)
            self._conn.commit()

    def insert(
        self,
        event_id: str,
        event_type: str,
        source: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_outbox (event_id, event_type, source, correlation_id, data)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (event_id) DO NOTHING
                """,
                (event_id, event_type, source, correlation_id, json.dumps(data)),
            )
            conn.commit()

    def fetch_pending(self, batch_size: int = 10) -> list[dict[str, Any]]:
        conn = self._get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, event_id, event_type, source, correlation_id, data, retry_count
                FROM event_outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT %s
                FOR UPDATE SKIP LOCKED
                """,
                (batch_size,),
            )
            return [dict(row) for row in cur.fetchall()]

    def mark_processing(self, record_id: int):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_outbox
                SET status = 'processing'
                WHERE id = %s
                """,
                (record_id,),
            )
            conn.commit()

    def mark_published(self, record_id: int):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_outbox
                SET status = 'processed', published_at = NOW()
                WHERE id = %s
                """,
                (record_id,),
            )
            conn.commit()

    def mark_patient_synced(self, patient_id: str):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE patients
                SET sync_status = 'SYNCED'
                WHERE id = %s
                """,
                (patient_id,),
            )
            conn.commit()

    def mark_failed(self, record_id: int, error: str):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE event_outbox
                SET status = 'failed', retry_count = retry_count + 1, last_error = %s
                WHERE id = %s
                """,
                (error, record_id),
            )
            conn.commit()

    def get_pending_count(self) -> int:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) as count FROM event_outbox WHERE status = 'pending'"
            )
            return cur.fetchone()[0]

    def cleanup_published(self, days: int = 7) -> int:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                DELETE FROM event_outbox
                WHERE status = 'processed' AND published_at < NOW() - INTERVAL '%s days'
                """,
                (days,),
            )
            deleted = cur.rowcount
            conn.commit()
            return deleted


outbox_store = OutboxStore()

