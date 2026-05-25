from typing import Any, Optional

from .base_publisher import BasePublisher


class PatientPublisher(BasePublisher):
    """Publica eventos del dominio paciente en patient.exchange."""

    async def patient_created(
        self,
        patient_id: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key="patient.created",
            event_id=f"patient.created.{patient_id}",
            event_type="patient.created",
            source="patient-service",
            data={"patient_id": patient_id, **data},
            correlation_id=correlation_id or patient_id,
        )

    async def patient_updated(
        self,
        patient_id: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key="patient.updated",
            event_id=f"patient.updated.{patient_id}",
            event_type="patient.updated",
            source="patient-service",
            data={"patient_id": patient_id, **data},
            correlation_id=correlation_id or patient_id,
        )
