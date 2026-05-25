from typing import Any, Optional

from .base_publisher import BasePublisher


class SyncPublisher(BasePublisher):
    """Publica eventos de sincronización entre nodos en sync.exchange."""

    async def sync_patient(
        self,
        patient_id: str,
        action: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key=f"sync.patient.{action}",
            event_id=f"sync.patient.{action}.{patient_id}",
            event_type=f"sync.patient.{action}",
            source="sync-service",
            data={"patient_id": patient_id, **data},
            correlation_id=correlation_id or patient_id,
        )

    async def sync_clinical(
        self,
        record_id: str,
        action: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key=f"sync.clinical.{action}",
            event_id=f"sync.clinical.{action}.{record_id}",
            event_type=f"sync.clinical.{action}",
            source="sync-service",
            data={"record_id": record_id, **data},
            correlation_id=correlation_id,
        )
