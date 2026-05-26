import json
import uuid
import psycopg2
import jwt as pyjwt
import datetime
from psycopg2.extras import RealDictCursor
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Any, List, Optional
import os

# ─── Auth router (prefix diferente para evitar duplicación) ────────────────────
auth_router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

JWT_SECRET = os.environ.get("JWT_SECRET_KEY", "super-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 8

# Demo credentials — for academic demo only
DEMO_USERS = {
    "admin": {"password": "admin123", "role": "admin", "name": "Administrador HIS"},
    "medico": {"password": "medico123", "role": "medico", "name": "Dr. Demo"},
    "enfermera": {"password": "enfermera123", "role": "enfermera", "name": "Enf. Demo"},
}


class LoginRequest(BaseModel):
    username: str
    password: str


@auth_router.post("/login")
async def login(req: LoginRequest):
    user = DEMO_USERS.get(req.username)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    now = datetime.datetime.utcnow()
    payload = {
        "sub": req.username,
        "role": user["role"],
        "name": user["name"],
        "iat": now,
        "exp": now + datetime.timedelta(hours=JWT_EXPIRE_HOURS),
    }
    token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": JWT_EXPIRE_HOURS * 3600,
        "user": {
            "username": req.username,
            "role": user["role"],
            "name": user["name"],
        },
    }


@auth_router.get("/me")
async def me_placeholder():
    """Placeholder — validated by JWTAuthMiddleware upstream."""
    return {"message": "Token válido"}


# ─── Main API router ────────────────────────────────────────────────────────────
router = APIRouter(prefix="/api", tags=["Real Backend API"])

DB_HOST = os.environ.get("LOCAL_DB_HOST", "pg_nodo1")
DB_PORT = 5432
DB_USER = "admin"
DB_PASS = "admin"
DB_NAME = "historia_clinica"
EVENTS_DB_NAME = "historia_clinica"

# Global states for demo
nodes_state = {
    "Sincelejo": "ACTIVO",
    "Bogotá": "ACTIVO",
    "Medellín": "ACTIVO"
}
cloud_state = "ACTIVO"

def get_db_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=DB_NAME)

def get_events_db_conn():
    return psycopg2.connect(host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS, dbname=EVENTS_DB_NAME)

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
            CREATE TABLE IF NOT EXISTS clinical_records (
                id SERIAL PRIMARY KEY,
                patient_id VARCHAR(64),
                sede VARCHAR(64),
                encounter_data JSONB,
                observation_data JSONB,
                condition_data JSONB,
                medication_data JSONB,
                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
            conn.commit()
        conn.close()
    except Exception as e:
        print("Error init tables", e)

# Run on import
init_tables()

class PatientData(BaseModel):
    sede: str
    documento: str
    nombres: str
    apellidos: str
    fecha_nacimiento: str
    sexo: str
    campos_clinicos: Optional[dict] = None

@router.get("/nodes/status")
async def get_nodes_status():
    return nodes_state

@router.post("/nodes/{node_id}/fail")
async def fail_node(node_id: str):
    nodes_state[node_id] = "OFFLINE"
    return {"success": True, "state": nodes_state}

@router.post("/nodes/{node_id}/restore")
async def restore_node(node_id: str):
    nodes_state[node_id] = "ACTIVO"
    return {"success": True, "state": nodes_state}

@router.post("/cloud/fail")
async def fail_cloud():
    global cloud_state
    cloud_state = "OFFLINE"
    return {"success": True, "cloud": cloud_state}

@router.post("/cloud/restore")
async def restore_cloud():
    global cloud_state
    cloud_state = "ACTIVO"
    return {"success": True, "cloud": cloud_state}

@router.get("/dashboard/status")
async def get_dashboard():
    import httpx
    import logging
    
    patients_count = {}
    events_count = {}
    patients_sync_status = {}
    
    try:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT sede, count(*) FROM patients GROUP BY sede")
        patients_count = dict(cur.fetchall())
        
        cur.execute("SELECT sync_status, count(*) FROM patients GROUP BY sync_status")
        patients_sync_status = dict(cur.fetchall())
        conn.close()
        
        conn_ev = get_events_db_conn()
        cur_ev = conn_ev.cursor()
        cur_ev.execute("SELECT LOWER(status), count(*) FROM event_outbox GROUP BY LOWER(status)")
        events_count = dict(cur_ev.fetchall())
        
        pending_by_node = {"sincelejo": 0, "bogotá": 0, "medellín": 0}
        processed_by_node = {"sincelejo": 0, "bogotá": 0, "medellín": 0}
        failed_by_node = {"sincelejo": 0, "bogotá": 0, "medellín": 0}

        cur_ev.execute("SELECT LOWER(status), LOWER(data->>'sede'), count(*) FROM event_outbox GROUP BY LOWER(status), LOWER(data->>'sede')")
        for status, sede, count in cur_ev.fetchall():
            if not sede: continue
            sede_key = sede.lower()
            if status == "pending":
                pending_by_node[sede_key] = pending_by_node.get(sede_key, 0) + count
            elif status == "processed":
                processed_by_node[sede_key] = processed_by_node.get(sede_key, 0) + count
            elif status == "failed":
                failed_by_node[sede_key] = failed_by_node.get(sede_key, 0) + count
                
        conn_ev.close()
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error fetching DB stats: {e}")

    hapi_fhir_count = 0
    hapi_fhir_online = False
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://hapi-fhir:8080/fhir/Patient?_summary=count")
            if resp.status_code == 200:
                hapi_fhir_online = True
                hapi_fhir_count = resp.json().get("total", 0)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error fetching from HAPI FHIR: {e}")

    any_offline = any(s == "OFFLINE" for s in nodes_state.values())
    mode = "CLOUD_OFFLINE" if cloud_state == "OFFLINE" else ("NODE_FAILURE" if any_offline else "HIBRIDO_NORMAL")
    
    return {
        "nodes": nodes_state,
        "cloud": "ACTIVO" if hapi_fhir_online else "OFFLINE",
        "patients": patients_count,
        "patients_sync": patients_sync_status,
        "pending_events": events_count.get("pending", 0),
        "processed_events": events_count.get("processed", 0),
        "failed_events": events_count.get("failed", 0),
        "pending_by_node": pending_by_node if 'pending_by_node' in locals() else {"sincelejo": 0, "bogotá": 0, "medellín": 0},
        "processed_by_node": processed_by_node if 'processed_by_node' in locals() else {"sincelejo": 0, "bogotá": 0, "medellín": 0},
        "failed_by_node": failed_by_node if 'failed_by_node' in locals() else {"sincelejo": 0, "bogotá": 0, "medellín": 0},
        "cloud_fhir_patients": hapi_fhir_count,
        "mode": mode
    }

@router.post("/patients")
async def create_patient(data: PatientData):
    if nodes_state.get(data.sede) == "OFFLINE":
        raise HTTPException(status_code=400, detail=f"Sede {data.sede} OFFLINE")
        
    patient_id = f"P-{uuid.uuid4().hex[:8]}"
    sync_status = "SINCRONIZADO" if cloud_state == "ACTIVO" else "PENDIENTE_SYNC"
    
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO patients (id, sede, documento, nombres, apellidos, fecha_nacimiento, sexo, sync_status, data) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (patient_id, data.sede, data.documento, data.nombres, data.apellidos, data.fecha_nacimiento, data.sexo, sync_status, json.dumps(data.campos_clinicos))
            )
            conn.commit()
        conn.close()
        
        # Outbox event
        event_id = f"EV-{uuid.uuid4().hex[:8]}"
        ev_status = "processed" if cloud_state == "ACTIVO" else "pending"
        conn_ev = get_events_db_conn()
        with conn_ev.cursor() as cur:
            cur.execute(
                "INSERT INTO event_outbox (event_id, event_type, source, data, status) VALUES (%s, %s, %s, %s, %s)",
                (event_id, "PatientCreated", "real_backend", json.dumps({"patient_id": patient_id, "sede": data.sede}), ev_status)
            )
            conn_ev.commit()
        conn_ev.close()
        
        return {"patient_id": patient_id, "sede": data.sede, "sync_status": sync_status, "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients")
async def get_patients():
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM patients ORDER BY created_at DESC")
            rows = cur.fetchall()
        conn.close()
        
        # Ensure dates are strings
        for row in rows:
            if row.get('created_at'):
                row['fecha_registro'] = row['created_at'].isoformat()
            row['estado_sync'] = row.get('sync_status')
            
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/patients/{patient_id}")
async def get_patient_detail(patient_id: str):
    try:
        conn = get_db_conn()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM patients WHERE id=%s OR documento=%s", (patient_id, patient_id))
            p = cur.fetchone()
            if not p:
                conn.close()
                raise HTTPException(status_code=404, detail="Paciente no encontrado")
                
            cur.execute("SELECT cr.*, e.status as event_status FROM clinical_records cr LEFT JOIN event_outbox e ON e.event_type = 'ClinicalRecordCreated' AND e.data->>'patient_id' = cr.patient_id AND cr.created_at >= e.created_at - interval '1 minute' AND cr.created_at <= e.created_at + interval '1 minute' WHERE cr.patient_id=%s ORDER BY cr.created_at ASC", (p["id"],))
            records = cur.fetchall()
            
            timeline = []
            for r in records:
                timeline.append({
                    "fecha": r["created_at"].isoformat() if r["created_at"] else None,
                    "encounter": r.get("encounter_data", {}),
                    "observation": r.get("observation_data", {}),
                    "condition": r.get("condition_data", {}),
                    "medication": r.get("medication_data", {}),
                    "status": r.get("event_status", "pending")
                })
            
            p["timeline"] = timeline
            if p.get("created_at"):
                p["fecha_registro"] = p["created_at"].isoformat()
            p["estado_sync"] = p.get("sync_status")
        conn.close()
        return p
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ClinicalRecord(BaseModel):
    patient_id: str
    sede: str
    encounter: dict
    observations: dict
    condition: dict
    medication_request: dict
    sync_mode: str = "local"
    created_at: str = None

@router.post("/clinical-records")
async def add_clinical_record(data: ClinicalRecord):
    try:
        conn = get_db_conn()
        with conn.cursor() as cur:
            enc_json = json.dumps(data.encounter)
            obs_json = json.dumps(data.observations)
            cond_json = json.dumps(data.condition)
            med_json = json.dumps(data.medication_request)
            
            cur.execute("""
                SELECT id FROM clinical_records 
                WHERE patient_id = %s 
                AND encounter_data::text = %s 
                AND observation_data::text = %s
                AND condition_data::text = %s
                AND medication_data::text = %s
                LIMIT 1
            """, (data.patient_id, enc_json, obs_json, cond_json, med_json))
            
            if cur.fetchone():
                return {"success": True, "event_id": "duplicate_skipped"}
                
            cur.execute(
                "INSERT INTO clinical_records (patient_id, sede, encounter_data, observation_data, condition_data, medication_data) VALUES (%s, %s, %s, %s, %s, %s)",
                (data.patient_id, data.sede, enc_json, obs_json, cond_json, med_json)
            )
            conn.commit()
        conn.close()
        
        event_id = f"EV-{uuid.uuid4().hex[:8]}"
        ev_status = "processed" if data.sync_mode == "sync" and cloud_state == "ACTIVO" else "pending"
        conn_ev = get_events_db_conn()
        with conn_ev.cursor() as cur:
            cur.execute(
                "INSERT INTO event_outbox (event_id, event_type, source, data, status) VALUES (%s, %s, %s, %s, %s)",
                (event_id, "ClinicalRecordCreated", "real_backend", json.dumps({
                    "patient_id": data.patient_id, 
                    "sede": data.sede,
                    "encounter": data.encounter,
                    "observations": data.observations,
                    "condition": data.condition,
                    "medication_request": data.medication_request
                }), ev_status)
            )
            conn_ev.commit()
        conn_ev.close()
        
        return {"success": True, "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync/process-pending")
async def process_pending():
    if cloud_state == "OFFLINE":
        raise HTTPException(status_code=400, detail="Cloud OFFLINE")
        
    try:
        conn_ev = get_events_db_conn()
        with conn_ev.cursor() as cur:
            cur.execute("UPDATE event_outbox SET status='processed' WHERE status='pending'")
            conn_ev.commit()
        conn_ev.close()
        
        conn = get_db_conn()
        with conn.cursor() as cur:
            cur.execute("UPDATE patients SET sync_status='SINCRONIZADO' WHERE sync_status='PENDIENTE_SYNC'")
            conn.commit()
        conn.close()
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
