import json
from fastapi import APIRouter, HTTPException

from ..models.clinical_models import (
    EncounterCreate,
    ObservationCreate,
    ConditionCreate,
    DischargeCreate,
    QueryRequest,
)
from ..services.distributed_repository import DistributedRepository
from ..services.event_dispatcher import event_dispatcher

router = APIRouter(prefix="/api/v1/clinical", tags=["Clinical Data"])
repo = DistributedRepository()


@router.on_event("shutdown")
async def shutdown():
    await event_dispatcher.close()


from pydantic import BaseModel
from typing import Optional, Dict, Any

class ClinicalRecordData(BaseModel):
    patient_id: str
    sede: str
    encounter: Optional[Dict[str, Any]] = None
    observations: Optional[Dict[str, Any]] = None
    condition: Optional[Dict[str, Any]] = None
    medication_request: Optional[Dict[str, Any]] = None

from ..services.clinical_repository import clinical_repository

@router.post("/record")
async def create_full_record(data: ClinicalRecordData):
    try:
        record_id = clinical_repository.create_clinical_record_with_outbox(
            patient_id=data.patient_id,
            sede=data.sede,
            record_data=data.dict()
        )
        return {"success": True, "message": "Registro clínico creado", "record_id": record_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/encounter")
async def create_encounter(data: EncounterCreate):
    try:
        result = repo.insert_encounter(data.dict(exclude_none=True))

        if result.get("success"):
            await event_dispatcher.publish_encounter_created(
                encounter_id=result["atencion_id"],
                data=json.loads(data.model_dump_json(exclude_none=True)),
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/observation")
async def create_observation(data: ObservationCreate):
    try:
        result = repo.insert_observation(data.dict(exclude_none=True))

        if result.get("success"):
            await event_dispatcher.publish_observation_created(
                observation_id=result["tecnologia_id"],
                data=json.loads(data.model_dump_json(exclude_none=True)),
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/condition")
async def create_condition(data: ConditionCreate):
    try:
        result = repo.insert_condition(data.dict(exclude_none=True))

        if result.get("success"):
            await event_dispatcher.publish_condition_created(
                condition_id=result["diagnostico_id"],
                data=json.loads(data.model_dump_json(exclude_none=True)),
            )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discharge")
async def create_discharge(data: DischargeCreate):
    try:
        result = repo.insert_discharge(data.dict(exclude_none=True))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def execute_query(request: QueryRequest):
    try:
        result = repo.execute_query_all_nodes(request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes")
async def get_nodes():
    return repo.check_node_health()


@router.get("/nodes/{node_id}")
async def get_node_detail(node_id: str):
    nodes = repo.check_node_health()
    for node in nodes:
        if node["id"].lower().replace(" ", "_") == node_id.lower():
            return node
    raise HTTPException(status_code=404, detail="Nodo no encontrado")


@router.get("/health/distributed")
async def distributed_health():
    nodes = repo.check_node_health()
    all_up = all(n["status"] == "running" for n in nodes)
    return {
        "status": "ok" if all_up else "degraded",
        "total_nodes": len(nodes),
        "nodes_up": sum(1 for n in nodes if n["status"] == "running"),
        "nodes": nodes,
    }
