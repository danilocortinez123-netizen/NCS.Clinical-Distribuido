from typing import Any, Optional

from .base_publisher import BasePublisher


class ClinicalPublisher(BasePublisher):
    """Publica eventos del dominio clínico en clinical.exchange."""

    async def encounter_created(
        self,
        encounter_id: int,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key="encounter.created",
            event_id=f"encounter.created.{encounter_id}",
            event_type="encounter.created",
            source="clinical-service",
            data={"encounter_id": str(encounter_id), **data},
            correlation_id=correlation_id,
        )

    async def observation_created(
        self,
        observation_id: str,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key="observation.created",
            event_id=f"observation.created.{observation_id}",
            event_type="observation.created",
            source="clinical-service",
            data={"observation_id": observation_id, **data},
            correlation_id=correlation_id,
        )

    async def condition_created(
        self,
        condition_id: int,
        data: dict[str, Any],
        correlation_id: Optional[str] = None,
    ):
        await self.publish(
            routing_key="condition.created",
            event_id=f"condition.created.{condition_id}",
            event_type="condition.created",
            source="clinical-service",
            data={"condition_id": str(condition_id), **data},
            correlation_id=correlation_id,
        )
