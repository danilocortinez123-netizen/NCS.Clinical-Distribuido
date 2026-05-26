import json
from fastapi import APIRouter, HTTPException
from typing import Any, Optional
from pydantic import BaseModel

from ..models.patient_model import PatientIdentificationData, PatientResponse
from ..transformers.fhir_transformer import FHIRTransformer
from ..services.fhir_client import FHIRClient
from ..services.patient_repository import patient_repository
from ..config import settings

router = APIRouter(prefix="/api/v1/patient", tags=["Patient"])
fhir_client = FHIRClient(settings.hapi_fhir_url)

class PatientDataLocal(BaseModel):
    documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: str
    sexo: str
    sede: str
    campos_clinicos: Optional[dict] = None

class ImportRequest(BaseModel):
    documento: str
    target_sede: str
    source: str
    fhir_resource: Optional[dict] = None

@router.post("/", response_model=PatientResponse)
async def create_patient(data: PatientDataLocal):
    try:
        # Save to PostgreSQL and Outbox in ONE transaction
        patient_id, event_payload = patient_repository.create_patient_with_outbox(
            patient_data=data.dict(),
            sede=data.sede
        )
        
        return PatientResponse(
            success=True,
            message="Paciente creado localmente y evento generado en outbox",
            patient_id=patient_id,
            fhir_resource={}, # No FHIR yet
            sede=data.sede,
            sync_status="PENDIENTE_SYNC",
            event_type="PatientCreated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear paciente: {str(e)}")

@router.get("/list")
async def list_patients(sede: Optional[str] = None, scope: Optional[str] = None):
    try:
        # If scope is network, ignore sede filter
        effective_sede = None if scope == "network" else sede
        patients = patient_repository.get_all_patients(effective_sede)
        
        return {
            "success": True, 
            "sede": sede,
            "scope": scope or "local",
            "patients": patients
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al listar pacientes: {str(e)}")

@router.get("/search/{identifier}")
async def search_patient(identifier: str, sede: Optional[str] = None):
    try:
        # 1. Search locally
        local_patient = patient_repository.get_patient_local(identifier, sede)
        if local_patient:
            if sede and local_patient.get("sede") and local_patient.get("sede").lower() != sede.lower():
                # Present in DB but belongs to another sede
                sync_status = local_patient.get("sync_status", "PENDIENTE_SYNC")
                # KEY RULE: Only SYNCED patients can be imported from other sedes
                if sync_status == "PENDIENTE_SYNC":
                    return {
                        "exists": True,
                        "found": True,
                        "source": "blocked",
                        "blocked_reason": "PENDIENTE_SYNC",
                        "message": f"Paciente no disponible en la red. Está pendiente de sincronización en su nodo origen ({local_patient.get('sede')}). Debe procesarse el Outbox primero.",
                        "patient": {"sede_origen": local_patient.get("sede"), "sync_status": sync_status},
                        "needs_import": False,
                        "already_local": False,
                        "available_fields": 0
                    }
                
                if sync_status == "IMPORTED_FROM_REMOTE":
                    return {
                        "exists": True,
                        "found": True,
                        "source": "local",
                        "needs_import": False,
                        "already_local": True,
                        "patient": local_patient
                    }

                # SINCRONIZADO: can be imported
                return {
                    "exists": True,
                    "found": True,
                    "source": "remote",
                    "remote_source": local_patient.get("sede"),
                    "needs_import": True,
                    "already_local": False,
                    "patient": local_patient,
                    "available_fields": 57
                }
            return {
                "exists": True,
                "found": True,
                "source": "local",
                "needs_import": False,
                "already_local": True,
                "patient": local_patient
            }
            
        # 2. If not found locally, search Cloud Core (HAPI FHIR)
        fhir_results = await fhir_client.search_by_identifier(identifier)
        if fhir_results.get("total", 0) > 0 and fhir_results.get("entry"):
            remote_patient = fhir_results["entry"][0]["resource"]
            return {
                "exists": True,
                "found": True,
                "source": "remote",
                "remote_source": "HAPI_FHIR",
                "needs_import": True,
                "already_local": False,
                "patient": remote_patient,
                "available_fields": 57
            }
            
        return {
            "exists": False,
            "found": False,
            "source": "none",
            "needs_import": False,
            "already_local": False,
            "message": "Paciente no encontrado. Puede registrarlo."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al buscar paciente: {str(e)}")

@router.post("/import")
async def import_patient(req: ImportRequest):
    try:
        import logging
        logging.info(f"[IMPORT] Iniciando importación de doc {req.documento} hacia sede destino real: {req.target_sede}")
        # Idempotency check: if already local or already imported
        local_patient = patient_repository.get_patient_local(req.documento)
        if local_patient:
            if local_patient.get("sede", "").lower() == req.target_sede.lower() or local_patient.get("sync_status") == "IMPORTED_FROM_REMOTE":
                return {
                    "success": True,
                    "message": "Paciente ya existe en esta sede. No se importó nuevamente.",
                    "already_local": True,
                    "needs_import": False,
                    "patient_id": local_patient.get("id")
                }

        # If FHIR resource is not provided, fetch it
        resource = req.fhir_resource
        if not resource:
            fhir_results = await fhir_client.search_by_identifier(req.documento)
            if fhir_results.get("total", 0) > 0 and fhir_results.get("entry"):
                resource = fhir_results["entry"][0]["resource"]
            else:
                raise HTTPException(status_code=404, detail="Paciente no encontrado en la fuente remota")
        
        # Fetch clinical records
        patient_fhir_id = resource.get("id")
        clinical_records = []
        if patient_fhir_id:
            import logging
            logging.info(f"[IMPORT] Buscando recursos para Patient/{patient_fhir_id}")
            try:
                encounters = await fhir_client.search_resource("Encounter", {"subject": f"Patient/{patient_fhir_id}"})
                observations = await fhir_client.search_resource("Observation", {"subject": f"Patient/{patient_fhir_id}"})
                conditions = await fhir_client.search_resource("Condition", {"subject": f"Patient/{patient_fhir_id}"})
                medications = await fhir_client.search_resource("MedicationRequest", {"subject": f"Patient/{patient_fhir_id}"})
                
                enc_total = encounters.get("total", 0)
                obs_total = observations.get("total", 0)
                cond_total = conditions.get("total", 0)
                med_total = medications.get("total", 0)
                
                logging.info(f"[IMPORT] Encontrados en FHIR: {enc_total} Encounter, {obs_total} Observation, {cond_total} Condition, {med_total} MedicationRequest")
                
                enc_entries = encounters.get("entry", [])
                obs_entries = observations.get("entry", [])
                cond_entries = conditions.get("entry", [])
                med_entries = medications.get("entry", [])
                
                records_by_encounter = {}
                standalone = {
                    "encounter": {},
                    "observation": {},
                    "condition": {},
                    "medication_request": {}
                }
                
                for e in enc_entries:
                    res = e.get("resource", {})
                    enc_id = res.get("id")
                    if enc_id:
                        records_by_encounter[f"Encounter/{enc_id}"] = {
                            "encounter": res,
                            "observation": {},
                            "condition": {},
                            "medication_request": {}
                        }
                
                for o in obs_entries:
                    res = o.get("resource", {})
                    enc_ref = res.get("encounter", {}).get("reference")
                    if enc_ref and enc_ref in records_by_encounter:
                        records_by_encounter[enc_ref]["observation"] = res
                    else:
                        standalone["observation"] = res

                for c in cond_entries:
                    res = c.get("resource", {})
                    enc_ref = res.get("encounter", {}).get("reference")
                    if enc_ref and enc_ref in records_by_encounter:
                        records_by_encounter[enc_ref]["condition"] = res
                    else:
                        standalone["condition"] = res
                        
                for m in med_entries:
                    res = m.get("resource", {})
                    enc_ref = res.get("encounter", {}).get("reference")
                    if enc_ref and enc_ref in records_by_encounter:
                        records_by_encounter[enc_ref]["medication_request"] = res
                    else:
                        standalone["medication_request"] = res
                
                clinical_records = list(records_by_encounter.values())
                if any(standalone.values()):
                    clinical_records.append(standalone)
            except Exception as e:
                logging.warning(f"Error fetching clinical records: {e}")
        
        resource["clinical_records"] = clinical_records
        
        patient_id, is_new = patient_repository.save_imported_patient(resource, req.source, req.target_sede)
        message = "Paciente importado correctamente" if is_new else "Paciente actualizado con historia clínica nueva"
        return {"success": True, "patient_id": patient_id, "message": message}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al importar paciente: {str(e)}")

@router.get("/{patient_id}")
async def get_patient(patient_id: str):
    try:
        local_patient = patient_repository.get_patient_local(patient_id)
        if not local_patient:
            raise HTTPException(status_code=404, detail="Paciente no encontrado localmente")
        return local_patient
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener paciente: {str(e)}")

@router.get("/health/fhir")
async def fhir_health():
    try:
        metadata = await fhir_client.check_health()
        return {"status": "ok", "fhir_version": metadata.get("fhirVersion"), "server": "HAPI FHIR"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"HAPI FHIR no disponible: {str(e)}")
