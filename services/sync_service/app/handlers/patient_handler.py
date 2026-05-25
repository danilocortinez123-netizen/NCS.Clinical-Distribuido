import logging
import httpx
from typing import Any
from ..config import settings
from ..transformers.fhir_transformer import FHIRTransformer

logger = logging.getLogger(__name__)

class PatientEventHandler:
    """Handlers para eventos del dominio paciente."""

    async def _send_to_fhir(self, resource_type: str, fhir_data: dict, method: str = "POST", resource_id: str = None):
        url = f"{settings.hapi_fhir_url}/{resource_type}"
        if method in ["PUT", "PATCH"] and resource_id:
            url = f"{url}/{resource_id}"
            
        async with httpx.AsyncClient() as client:
            if method == "POST":
                response = await client.post(url, json=fhir_data)
            elif method == "PUT":
                response = await client.put(url, json=fhir_data)
                
            response.raise_for_status()
            return response.json()

    async def handle_created(self, body: dict[str, Any]) -> dict[str, Any]:
        event_id = body.get("event_id")
        data = body.get("data", {})
        patient_id = data.get("patient_id")

        logger.info(f"[PATIENT_CREATED] Procesando evento para sincronizar paciente {patient_id} a HAPI FHIR")
        
        try:
            import json
            # Transform to FHIR
            fhir_patient = FHIRTransformer.to_fhir_patient(data)
            
            # Serialize model to JSON string, then parse to dict to ensure all objects (like dates) are JSON primitives
            fhir_json_str = fhir_patient.json(exclude_none=True)
            fhir_data = json.loads(fhir_json_str)
            
            # Add id to resource and send to HAPI FHIR using PUT to ensure consistent ID
            fhir_data["id"] = patient_id
            result = await self._send_to_fhir("Patient", fhir_data, "PUT", patient_id)
            
            logger.info(f"[SYNC_SUCCESS] Paciente {patient_id} sincronizado exitosamente a HAPI FHIR con ID {result.get('id')}")
            return {"status": "ok", "patient_id": patient_id, "fhir_id": result.get("id")}
        except httpx.HTTPStatusError as e:
            logger.error(f"[SYNC_FAILED] Falló sincronización para paciente {patient_id}: {str(e)}. Detalles: {e.response.text}")
            raise e
        except Exception as e:
            logger.error(f"[SYNC_FAILED] Falló sincronización para paciente {patient_id}: {str(e)}")
            raise e

    async def handle_updated(self, body: dict[str, Any]) -> dict[str, Any]:
        event_id = body.get("event_id")
        data = body.get("data", {})
        patient_id = data.get("patient_id")

        logger.info(f"[PATIENT_UPDATED] Paciente {patient_id} actualizado")
        return {"status": "ok", "patient_id": patient_id}

    async def handle_sync(self, body: dict[str, Any]) -> dict[str, Any]:
        data = body.get("data", {})
        patient_id = data.get("patient_id")
        logger.info(f"[SYNC_PATIENT] Replicando paciente {patient_id} entre nodos")
        return {"status": "ok", "patient_id": patient_id}

patient_handler = PatientEventHandler()
