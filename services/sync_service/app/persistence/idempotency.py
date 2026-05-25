import logging
from datetime import datetime, timedelta
from typing import Optional

import psycopg2
import psycopg2.extras

from ..config import settings

logger = logging.getLogger(__name__)


class IdempotencyStore:
    """Almacén de idempotencia basado en PostgreSQL.
    
    Previene procesamiento duplicado de eventos usando event_id como clave única.
    Limpieza automática de registros mayores a 7 días.
    """

    def __init__(self):
        self._conn = None
        self._ttl_days = 7

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
                CREATE TABLE IF NOT EXISTS event_idempotency (
                    event_id VARCHAR(64) PRIMARY KEY,
                    event_type VARCHAR(64) NOT NULL,
                    status VARCHAR(16) NOT NULL DEFAULT 'processed',
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP DEFAULT (NOW() + INTERVAL '7 days')
                )
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_idempotency_expires
                ON event_idempotency (expires_at)
            """)
            self._conn.commit()

    def is_processed(self, event_id: str) -> bool:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM event_idempotency WHERE event_id = %s",
                (event_id,),
            )
            return cur.fetchone() is not None

    def mark_processed(self, event_id: str, event_type: str):
        conn = self._get_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO event_idempotency (event_id, event_type, status)
                    VALUES (%s, %s, 'processed')
                    ON CONFLICT (event_id) DO NOTHING
                    """,
                    (event_id, event_type),
                )
                conn.commit()
                logger.info(f"Idempotency marked: {event_type}[{event_id}]")
        except Exception as e:
            logger.error(f"Idempotency insert failed: {e}", exc_info=True)

    def mark_failed(self, event_id: str, event_type: str):
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO event_idempotency (event_id, event_type, status)
                VALUES (%s, %s, 'failed')
                ON CONFLICT (event_id) DO UPDATE SET status = 'failed'
                """,
                (event_id, event_type),
            )
            conn.commit()

    def cleanup_expired(self) -> int:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM event_idempotency WHERE expires_at < NOW()"
            )
            deleted = cur.rowcount
            conn.commit()
            if deleted:
                logger.info(f"Limpieza idempotencia: {deleted} registros eliminados")
            return deleted

    def get_stats(self) -> dict:
        conn = self._get_conn()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                SELECT status, COUNT(*) as count
                FROM event_idempotency
                GROUP BY status
                """
            )
            rows = cur.fetchall()
            cur.execute("SELECT COUNT(*) as total FROM event_idempotency")
            total = cur.fetchone()["total"]
            return {
                "total": total,
                "by_status": {r["status"]: r["count"] for r in rows},
            }

    def close(self):
        if self._conn and not self._conn.closed:
            self._conn.close()


idempotency_store = IdempotencyStore()
