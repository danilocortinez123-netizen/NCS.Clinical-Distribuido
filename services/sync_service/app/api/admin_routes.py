from fastapi import APIRouter

from ..persistence.idempotency import idempotency_store
from ..persistence.outbox import outbox_store
from ..consumers.base_consumer import BaseConsumer
from ..broker.exchange_setup import QUEUE_CONFIG

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@router.get("/idempotency/stats")
async def idempotency_stats():
    return idempotency_store.get_stats()


@router.post("/idempotency/cleanup")
async def cleanup_idempotency():
    deleted = idempotency_store.cleanup_expired()
    return {"deleted": deleted, "message": "Registros expirados eliminados"}


@router.get("/outbox/pending")
async def pending_events():
    count = outbox_store.get_pending_count()
    return {"pending_count": count}

@router.post("/outbox/process-pending")
async def process_pending():
    from ..persistence.outbox_poller import outbox_poller
    try:
        await outbox_poller._poll_once()
        return {"success": True, "message": "Proceso manual completado"}
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("Error en process-pending manual")
        return {"success": False, "error": str(e)}


@router.get("/outbox/stats")
async def outbox_stats():
    import psycopg2.extras
    conn = outbox_store._get_conn()
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT status, COUNT(*) as count
            FROM event_outbox
            GROUP BY status
        """)
        by_status = {r["status"]: r["count"] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) as total FROM event_outbox")
        total = cur.fetchone()["total"]
    return {"total": total, "by_status": by_status}


@router.get("/topology/queues")
async def list_queues():
    queues = {}
    for name, config in QUEUE_CONFIG.items():
        queues[name] = {
            "exchange": config.get("exchange"),
            "routing_key": config.get("routing_key"),
            "dlq": config.get("dlq"),
            "durable": config.get("durable"),
        }
    return queues


@router.get("/topology/exchanges")
async def list_exchanges():
    from ..broker.exchange_setup import EXCHANGE_CONFIG
    return {
        name: {
            "type": config["type"].value,
            "routing_keys": config["routing_keys"],
        }
        for name, config in EXCHANGE_CONFIG.items()
    }

@router.get("/dashboard/status")
async def dashboard_status():
    import psycopg2.extras
    import httpx
    import logging
    
    conn = outbox_store._get_conn()
    
    sedes_summary = {}
    outbox_summary = {"pending": 0, "processed": 0, "failed": 0}
    patients_sync_status = {}
    
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # Patients by sede
            cur.execute("SELECT sede, COUNT(*) as count FROM patients GROUP BY sede")
            for r in cur.fetchall():
                sedes_summary.setdefault(r["sede"], {})["patients"] = r["count"]
                
            # Clinical records by sede
            cur.execute("SELECT sede, COUNT(*) as count FROM clinical_records GROUP BY sede")
            for r in cur.fetchall():
                sedes_summary.setdefault(r["sede"], {})["clinical_records"] = r["count"]
                
            # Ensure default keys
            for s in ["Sincelejo", "Bogotá", "Medellín"]:
                if s not in sedes_summary:
                    sedes_summary[s] = {"patients": 0, "clinical_records": 0}
                if "patients" not in sedes_summary[s]: sedes_summary[s]["patients"] = 0
                if "clinical_records" not in sedes_summary[s]: sedes_summary[s]["clinical_records"] = 0
                
            # Outbox summary
            cur.execute("SELECT status, COUNT(*) as count FROM event_outbox GROUP BY status")
            for r in cur.fetchall():
                outbox_summary[r["status"]] = r["count"]
                
            # Patients sync status
            cur.execute("SELECT sync_status, COUNT(*) as count FROM patients GROUP BY sync_status")
            for r in cur.fetchall():
                patients_sync_status[r["sync_status"]] = r["count"]
                
    except Exception as e:
        logging.getLogger(__name__).exception("Error fetching dashboard stats")
    finally:
        conn.close()
        
    # Fetch real count from HAPI FHIR
    hapi_fhir_count = 0
    hapi_fhir_online = False
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://hapi-fhir:8080/fhir/Patient?_summary=count")
            if resp.status_code == 200:
                hapi_fhir_online = True
                hapi_fhir_count = resp.json().get("total", 0)
    except Exception as e:
        logging.getLogger(__name__).warning(f"Error fetching from HAPI FHIR: {e}")
        
    return {
        "sedes": sedes_summary,
        "outbox": outbox_summary,
        "patients_sync": patients_sync_status,
        "cloud": {
            "hapi_fhir": "online" if hapi_fhir_online else "offline",
            "fhir_patient_count": hapi_fhir_count
        }
    }

@router.get("/dashboard/recent-events")
async def recent_events():
    import psycopg2.extras
    conn = outbox_store._get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT event_id, event_type, source, correlation_id, status, retry_count, created_at, published_at, last_error, data->>'sede' as sede FROM event_outbox ORDER BY created_at DESC LIMIT 10")
            events = cur.fetchall()
            return {"success": True, "events": events}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        conn.close()
