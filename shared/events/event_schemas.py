from pydantic import BaseModel
from typing import Any, Optional
from datetime import datetime
import uuid


class DomainEvent(BaseModel):
    event_id: str
    event_type: str
    source: str
    timestamp: str
    data: dict[str, Any]
    correlation_id: Optional[str] = None


class PatientCreatedEvent(DomainEvent):
    @classmethod
    def create(cls, patient_id: str, data: dict[str, Any]) -> "PatientCreatedEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="patient.created",
            source="patient-service",
            timestamp=datetime.utcnow().isoformat(),
            data={"patient_id": patient_id, **data},
            correlation_id=patient_id,
        )


class PatientUpdatedEvent(DomainEvent):
    @classmethod
    def create(cls, patient_id: str, data: dict[str, Any]) -> "PatientUpdatedEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="patient.updated",
            source="patient-service",
            timestamp=datetime.utcnow().isoformat(),
            data={"patient_id": patient_id, **data},
            correlation_id=patient_id,
        )


class EncounterCreatedEvent(DomainEvent):
    @classmethod
    def create(cls, encounter_id: str, data: dict[str, Any]) -> "EncounterCreatedEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="clinical.encounter.created",
            source="clinical-service",
            timestamp=datetime.utcnow().isoformat(),
            data={"encounter_id": encounter_id, **data},
            correlation_id=encounter_id,
        )


class ObservationCreatedEvent(DomainEvent):
    @classmethod
    def create(cls, observation_id: str, data: dict[str, Any]) -> "ObservationCreatedEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="clinical.observation.created",
            source="clinical-service",
            timestamp=datetime.utcnow().isoformat(),
            data={"observation_id": observation_id, **data},
            correlation_id=observation_id,
        )


class ConditionCreatedEvent(DomainEvent):
    @classmethod
    def create(cls, condition_id: str, data: dict[str, Any]) -> "ConditionCreatedEvent":
        return cls(
            event_id=str(uuid.uuid4()),
            event_type="clinical.condition.created",
            source="clinical-service",
            timestamp=datetime.utcnow().isoformat(),
            data={"condition_id": condition_id, **data},
            correlation_id=condition_id,
        )
