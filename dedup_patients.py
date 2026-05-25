import psycopg2
from psycopg2.extras import RealDictCursor
import json
import os

def get_db_conn():
    return psycopg2.connect(host="pg_nodo1", port=5432, user="admin", password="admin", dbname="historia_clinica")

def dedup():
    conn = get_db_conn()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get duplicates
    cur.execute("SELECT documento, COUNT(*) FROM patients GROUP BY documento HAVING COUNT(*) > 1")
    dupes = cur.fetchall()
    
    report_lines = []
    report_lines.append("# Reporte de Deduplicación de Pacientes\n")
    
    total_deleted = 0
    total_reassigned_cr = 0
    total_reassigned_ev = 0
    
    for dupe in dupes:
        doc = dupe['documento']
        cur.execute("SELECT * FROM patients WHERE documento = %s ORDER BY created_at DESC", (doc,))
        patients = cur.fetchall()
        
        # Sort by preference
        def sort_key(p):
            status = p['sync_status']
            score = 0
            if status == 'SYNCED' or status == 'SINCRONIZADO':
                score = 3
            elif status == 'IMPORTED_FROM_REMOTE':
                score = 2
            else:
                score = 1
            return score
            
        patients.sort(key=sort_key, reverse=True)
        
        kept = patients[0]
        deleted = patients[1:]
        
        kept_id = kept['id']
        
        report_lines.append(f"## Documento: {doc}")
        report_lines.append(f"- **Conservado:** `{kept_id}` (Estado: {kept['sync_status']})")
        
        for d in deleted:
            d_id = d['id']
            report_lines.append(f"- **Eliminado:** `{d_id}` (Estado: {d['sync_status']})")
            total_deleted += 1
            
            # 3. Reassign clinical_records
            cur.execute("UPDATE clinical_records SET patient_id = %s WHERE patient_id = %s", (kept_id, d_id))
            reassigned_cr = cur.rowcount
            if reassigned_cr > 0:
                report_lines.append(f"  - Reasignadas {reassigned_cr} historias clínicas.")
                total_reassigned_cr += reassigned_cr
            
            # 4. Reassign event_outbox by correlation_id
            cur.execute("UPDATE event_outbox SET correlation_id = %s WHERE correlation_id = %s", (kept_id, d_id))
            
            # Reassign event_outbox by data payload
            cur.execute("SELECT id, data FROM event_outbox WHERE data->>'patient_id' = %s", (d_id,))
            events = cur.fetchall()
            for ev in events:
                data = ev['data']
                data['patient_id'] = kept_id
                cur.execute("UPDATE event_outbox SET data = %s::jsonb WHERE id = %s", (json.dumps(data), ev['id']))
                
            if len(events) > 0:
                report_lines.append(f"  - Reasignados {len(events)} eventos en outbox.")
                total_reassigned_ev += len(events)
                
            # Delete patient
            cur.execute("DELETE FROM patients WHERE id = %s", (d_id,))
            
    conn.commit()
    conn.close()
    
    report_lines.append(f"\n### Resumen\n")
    report_lines.append(f"- Pacientes eliminados: {total_deleted}")
    report_lines.append(f"- Historias clínicas reasignadas: {total_reassigned_cr}")
    report_lines.append(f"- Eventos reasignados: {total_reassigned_ev}")
    
    with open("/tmp/DEDUP_REPORT.md", "w") as f:
        f.write("\n".join(report_lines))
    print("Deduplicación completada.")

if __name__ == '__main__':
    dedup()
