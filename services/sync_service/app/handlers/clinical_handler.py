import logging
from typing import Any

logger = logging.getLogger(__name__)


class ClinicalEventHandler:
    """Handlers para eventos del dominio clínico."""

    async def handle_encounter_created(self, body: dict[str, Any]) -> dict[str, Any]:
        event_id = body.get("event_id")
        data = body.get("data", {})
        encounter_id = data.get("encounter_id")

        logger.info(f"[ENCOUNTER_CREATED] Encuentro {encounter_id} registrado")
        logger.info(f"[AUDIT] event_id={event_id}, encounter_id={encounter_id}")

        return {"status": "ok", "encounter_id": encounter_id}

    async def handle_observation_created(self, body: dict[str, Any]) -> dict[str, Any]:
        event_id = body.get("event_id")
        data = body.get("data", {})
        observation_id = data.get("observation_id")

        logger.info(f"[OBSERVATION_CREATED] Observación {observation_id} registrada")
        logger.info(f"[AUDIT] event_id={event_id}, observation_id={observation_id}")

        return {"status": "ok", "observation_id": observation_id}

    async def handle_condition_created(self, body: dict[str, Any]) -> dict[str, Any]:
        event_id = body.get("event_id")
        data = body.get("data", {})
        condition_id = data.get("condition_id")

        logger.info(f"[CONDITION_CREATED] Condición {condition_id} registrada")
        logger.info(f"[AUDIT] event_id={event_id}, condition_id={condition_id}")

        return {"status": "ok", "condition_id": condition_id}

    async def _send_to_fhir(self, resource_type: str, fhir_data: dict, method: str = "POST", resource_id: str = None):
        import httpx
        from ..config import settings
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

    async def handle_sync(self, body: dict[str, Any]) -> dict[str, Any]:
        data = body.get("data", {})
        record_id = data.get("record_id")
        patient_id = data.get("patient_id")

        logger.info(f"[SYNC_CLINICAL] Sincronizando registro clínico {record_id} a HAPI FHIR")
        
        try:
            patient_id = data.get("patient_id")
            
            # Encounter
            enc_data = data.get("encounter", {})
            encounter_fhir = {
                "resourceType": "Encounter",
                "status": "finished",
                "class": {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                    "code": "AMB"
                },
                "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": enc_data.get("fecha_ingreso")},
                "reasonCode": [{"text": enc_data.get("causa_atencion")}]
            }
            enc_res = await self._send_to_fhir("Encounter", encounter_fhir, "POST")
            enc_id = enc_res.get("id")

            # Observation
            obs_data = data.get("observations", {})
            if obs_data:
                observation_fhir = {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {"text": "Observación Clínica"},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "valueString": str(obs_data)
                }
                await self._send_to_fhir("Observation", observation_fhir, "POST")

            # Condition
            cond_data = data.get("condition", {})
            if cond_data:
                condition_fhir = {
                    "resourceType": "Condition",
                    "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "code": {"text": cond_data.get("diagnostico_ingreso", "Diagnóstico General")}
                }
                await self._send_to_fhir("Condition", condition_fhir, "POST")

            # MedicationRequest
            med_data = data.get("medication_request", {})
            if med_data:
                medication_fhir = {
                    "resourceType": "MedicationRequest",
                    "status": "active",
                    "intent": "order",
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "encounter": {"reference": f"Encounter/{enc_id}"},
                    "medicationCodeableConcept": {"text": med_data.get("descripcion_medicamento", "Medicamento recetado")}
                }
                await self._send_to_fhir("MedicationRequest", medication_fhir, "POST")

            logger.info(f"[SYNC_SUCCESS] Historia Clínica de paciente {patient_id} sincronizada a HAPI FHIR")
            return {"status": "ok", "record_id": record_id}
        except Exception as e:
            logger.error(f"[SYNC_FAILED] Falló sincronización de registro clínico: {str(e)}")
            raise e


clinical_handler = ClinicalEventHandler()
