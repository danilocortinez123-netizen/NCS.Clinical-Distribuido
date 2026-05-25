import logging
from typing import Any

logger = logging.getLogger(__name__)


class SyncEventHandler:
    """Handlers para eventos de sincronización entre nodos."""

    async def handle_patient_sync(self, body: dict[str, Any]) -> dict[str, Any]:
        data = body.get("data", {})
        patient_id = data.get("patient_id")
        action = body.get("event_type", "unknown").split(".")[-1]

        logger.info(
            f"[SYNC] Replicación paciente {patient_id} "
            f"(acción: {action}) entre nodos PostgreSQL"
        )

        return {"status": "ok", "target": "pg_nodos"}

    async def handle_clinical_sync(self, body: dict[str, Any]) -> dict[str, Any]:
        data = body.get("data", {})
        record_id = data.get("record_id")

        logger.info(f"[SYNC] Replicación registro clínico {record_id} entre nodos")

        return {"status": "ok", "target": "pg_nodos"}

    async def handle_health_check(self, body: dict[str, Any]) -> dict[str, Any]:
        logger.info("[SYNC] Health check de replicación recibido")
        return {"status": "ok", "service": "sync-service"}


sync_handler = SyncEventHandler()
