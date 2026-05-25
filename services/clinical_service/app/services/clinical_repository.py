import json
import psycopg2
from typing import Any
from ..config import settings

def get_db_conn():
    return psycopg2.connect(
        host=settings.events_db_host,
        port=settings.events_db_port,
        user=settings.events_db_user,
        password=settings.events_db_password,
        dbname="historia_clinica",
    )

class ClinicalRepository:
    def create_clinical_record_with_outbox(self, patient_id: str, sede: str, record_data: dict):
        conn = get_db_conn()
        event_id = f"evt-clin-{patient_id}-{__import__('uuid').uuid4().hex[:6]}"
        
        try:
            with conn.cursor() as cur:
                # 1. Insert Record
                cur.execute(
                    """
                    INSERT INTO clinical_records (patient_id, sede, encounter_data, observation_data, condition_data, medication_data)
                    VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
                    RETURNING id
                    """,
                    (
                        patient_id,
                        sede,
                        json.dumps(record_data.get("encounter", {})),
                        json.dumps(record_data.get("observations", {})),
                        json.dumps(record_data.get("condition", {})),
                        json.dumps(record_data.get("medication_request", {}))
                    )
                )
                record_id = cur.fetchone()[0]
                
                # 2. Insert Outbox Event
                event_payload = {
                    "patient_id": patient_id,
                    "sede": sede,
                    "record_id": record_id,
                    **record_data
                }
                
                cur.execute(
                    """
                    INSERT INTO event_outbox (event_id, event_type, source, correlation_id, data)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (event_id, "clinical.created", "clinical-service", patient_id, json.dumps(event_payload))
                )
                
            conn.commit()
            return record_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

clinical_repository = ClinicalRepository()
