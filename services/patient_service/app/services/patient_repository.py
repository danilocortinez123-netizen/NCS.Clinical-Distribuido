import json
import uuid
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Any, Optional
from ..config import settings

def get_db_conn():
    return psycopg2.connect(
        host=settings.events_db_host,
        port=settings.events_db_port,
        user=settings.events_db_user,
        password=settings.events_db_password,
        dbname="historia_clinica", # FORCE to historia_clinica for single transaction
    )

def init_tables():
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id VARCHAR(64) PRIMARY KEY,
                sede VARCHAR(64),
                documento VARCHAR(64),
                nombres VARCHAR(128),
                apellidos VARCHAR(128),
                fecha_nacimiento VARCHAR(64),
                sexo VARCHAR(64),
                sync_status VARCHAR(64) DEFAULT 'PENDIENTE_SYNC',
                data JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
            cur.execute("""
            CREATE TABLE IF NOT EXISTS event_outbox (
                id SERIAL PRIMARY KEY,
                event_id VARCHAR(64) NOT NULL UNIQUE,
                event_type VARCHAR(64) NOT NULL,
                source VARCHAR(64) NOT NULL,
                correlation_id VARCHAR(64),
                data JSONB NOT NULL,
                status VARCHAR(16) NOT NULL DEFAULT 'pending',
                retry_count INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                published_at TIMESTAMP,
                last_error TEXT
            );
            """)
            conn.commit()
        conn.close()
    except Exception as e:
        print("Error init tables patient repo:", e)

init_tables()

class PatientRepository:
    def create_patient_with_outbox(self, patient_data: dict, sede: str):
        conn = get_db_conn()
        patient_id = f"P-{uuid.uuid4().hex[:8]}"
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        
        documento = patient_data.get("documento", "")
        nombres = patient_data.get("nombres", "")
        apellidos = patient_data.get("apellidos", "")
        fecha_nacimiento = patient_data.get("fecha_nacimiento", "")
        sexo = patient_data.get("sexo", "")
        
        event_payload = {
            "patient_id": patient_id,
            "sede": sede,
            **patient_data
        }
        
        try:
            with conn.cursor() as cur:
                # 1. Insert Patient
                cur.execute(
                    """
                    INSERT INTO patients (id, sede, documento, nombres, apellidos, fecha_nacimiento, sexo, sync_status, data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'PENDIENTE_SYNC', %s::jsonb)
                    """,
                    (patient_id, sede, documento, nombres, apellidos, fecha_nacimiento, sexo, json.dumps(patient_data))
                )
                
                # 2. Insert Outbox Event
                cur.execute(
                    """
                    INSERT INTO event_outbox (event_id, event_type, source, correlation_id, data)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (event_id, "patient.created", "patient-service", patient_id, json.dumps(event_payload))
                )
                
            conn.commit()
            return patient_id, event_payload
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_patient_local(self, identifier: str, sede: Optional[str] = None):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if sede:
                    cur.execute("SELECT * FROM patients WHERE documento = %s OR id = %s ORDER BY (sede = %s) DESC", (identifier, identifier, sede))
                else:
                    cur.execute("SELECT * FROM patients WHERE documento = %s OR id = %s", (identifier, identifier))
                return cur.fetchone()
        finally:
            conn.close()

    def get_all_patients(self, sede: Optional[str] = None):
        conn = get_db_conn()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                if sede:
                    cur.execute("SELECT id, documento, nombres, apellidos, sede, sync_status, created_at FROM patients WHERE sede = %s ORDER BY created_at DESC", (sede,))
                else:
                    cur.execute("SELECT id, documento, nombres, apellidos, sede, sync_status, created_at FROM patients ORDER BY created_at DESC")
                return cur.fetchall()
        finally:
            conn.close()

    def save_imported_patient(self, fhir_resource: dict, source_sede: str, target_sede: str):
        conn = get_db_conn()
        patient_id = fhir_resource.get("id", f"P-{uuid.uuid4().hex[:8]}")
        event_id = f"evt-{uuid.uuid4().hex[:8]}"
        
        # Extract basic info from FHIR
        identifiers = fhir_resource.get("identifier", [])
        documento = identifiers[0].get("value", "") if identifiers else ""
        names = fhir_resource.get("name", [])
        nombres = names[0].get("given", [""])[0] if names and "given" in names[0] else (names[0].get("text", "") if names else "")
        apellidos = names[0].get("family", "") if names and "family" in names[0] else ""
        fecha_nacimiento = fhir_resource.get("birthDate", "")
        sexo = fhir_resource.get("gender", "")
        
        event_payload = {
            "event_type": "PatientImportedFromRemoteSite",
            "source_site": source_sede,
            "target_site": target_sede,
            "patient_id": patient_id,
            "document_number": documento,
        }
        
        try:
            with conn.cursor() as cur:
                # Upsert Patient Check
                cur.execute("SELECT id FROM patients WHERE id = %s OR documento = %s LIMIT 1", (patient_id, documento))
                row = cur.fetchone()
                
                is_new_patient = False
                if row:
                    existing_id = row[0] if isinstance(row, tuple) else row['id'] if isinstance(row, dict) else row
                    cur.execute(
                        """
                        UPDATE patients 
                        SET nombres = %s, apellidos = %s, fecha_nacimiento = %s, sexo = %s, sync_status = 'IMPORTED_FROM_REMOTE', data = %s::jsonb 
                        WHERE id = %s
                        """,
                        (nombres, apellidos, fecha_nacimiento, sexo, json.dumps(fhir_resource), existing_id)
                    )
                    patient_id = existing_id
                else:
                    cur.execute(
                        """
                        INSERT INTO patients (id, sede, documento, nombres, apellidos, fecha_nacimiento, sexo, sync_status, data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'IMPORTED_FROM_REMOTE', %s::jsonb)
                        """,
                        (patient_id, target_sede, documento, nombres, apellidos, fecha_nacimiento, sexo, json.dumps(fhir_resource))
                    )
                    is_new_patient = True
                
                cur.execute(
                    """
                    INSERT INTO event_outbox (event_id, event_type, source, correlation_id, data)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    """,
                    (event_id, "patient.imported", "patient-service", patient_id, json.dumps(event_payload))
                )
                
                # Import clinical records preventing duplicates
                clinical_records = fhir_resource.get("clinical_records", [])
                for rec in clinical_records:
                    enc_json = json.dumps(rec.get("encounter", {}))
                    obs_json = json.dumps(rec.get("observation", {}))
                    cond_json = json.dumps(rec.get("condition", {}))
                    med_json = json.dumps(rec.get("medication_request", {}))
                    
                    # Check existing exact match
                    cur.execute("""
                        SELECT id FROM clinical_records 
                        WHERE patient_id = %s 
                        AND encounter_data::text = %s 
                        AND observation_data::text = %s
                        AND condition_data::text = %s
                        AND medication_data::text = %s
                        LIMIT 1
                    """, (patient_id, enc_json, obs_json, cond_json, med_json))
                    
                    if cur.fetchone():
                        continue # Skip duplicate
                        
                    cur.execute(
                        """
                        INSERT INTO clinical_records (patient_id, sede, encounter_data, observation_data, condition_data, medication_data)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (patient_id, target_sede, enc_json, obs_json, cond_json, med_json)
                    )
                    
            conn.commit()
            return patient_id, is_new_patient
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

patient_repository = PatientRepository()
