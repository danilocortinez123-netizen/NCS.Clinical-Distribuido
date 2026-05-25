# AUDITORÍA RÚBRICA — HIS Distribuido v3.0
Generado: 2026-05-25

## ✅ CUMPLE COMPLETAMENTE

### 1. Docker Compose
- Servicios: gateway, patient, clinical, sync, 3xPostgreSQL, RabbitMQ, HAPI FHIR
- Healthchecks en pg_nodo1/2/3 y rabbitmq
- restart: unless-stopped en todos
- Red interna historia_clinica_net
- Volúmenes: pg_data_nodo1/2/3

### 2. Tres Nodos Distribuidos
- Sincelejo (5433), Bogotá (5434), Medellín (5435)
- Selector global de sede en sessionStorage
- Dashboard por nodo con KPIs separados

### 3. Regla de Sincronización (NUEVA)
- PENDIENTE_SYNC en Sede A → NO importable desde Sede B
- Mensaje: "Paciente no disponible en la red. Está pendiente..."
- Solo SINCRONIZADO permite importación

### 4. Outbox Pattern
- event_outbox: pending / processed / failed
- Transacción atómica paciente + evento
- Endpoint POST /api/sync/process-pending

### 5. HAPI FHIR R4
- http://localhost:8080 activo
- Recursos: Patient, Encounter, Observation, Condition, MedicationRequest
- Dashboard muestra count real de FHIR

### 6. Historia Clínica 57 Campos
- Wizard 6 tabs, campos reglamentarios
- Desplegables clínicos CIE-10, CUPS, EPS, medicamentos
- Generador de prueba con 5 casos reales

### 7. Generador de Datos de Prueba (NUEVO)
- Botón en Registro Paciente y Carga HC
- 5 casos: IRA, Dolor abdominal, HTA, Cefalea, Gastritis

### 8. Interfaces Clínicas
- /registro-paciente — Admisión 57 campos
- /carga-hc — Clínico/diagnóstico/prescripción
- /consulta-hc — Búsqueda con regla de sync
- /paciente/{id} — Línea de tiempo clínica
- / — Dashboard KPIs + outbox por nodo

### 9. Tolerancia a Fallos
- Panel simulación en dashboard
- Endpoints: POST /api/nodes/{node}/fail|restore
- Bloqueo real en backend si nodo OFFLINE (HTTP 400)

## ⚠️ CUMPLE PARCIALMENTE

### Base de datos distribuida
- No hay replicación streaming entre nodos
- ARGUMENTO: Consistencia eventual por Outbox + HAPI FHIR como fuente de verdad
- Los 3 nodos están separados: 5433/5434/5435

### Tolerancia a fallos persistente
- Estado fallo en memoria (se pierde si contenedor se reinicia)
- ARGUMENTO: Simulación lógica para demo académica. Comportamiento coherente.

### 10. Observabilidad (Prometheus y Grafana)
- Métricas de FastAPI (Instrumentator)
- Métricas Custom del Outbox Pattern (Eventos procesados, fallidos, pendientes por nodo)
- Exporters de PostgreSQL (1, 2 y 3)
- Métricas de RabbitMQ activadas
- Dashboards auto-aprovisionados en Grafana

## ❌ NO IMPLEMENTADO

### Replicación PostgreSQL real
- ARGUMENTO: Sharding por sede es estrategia válida de distribución

## 📁 ARCHIVOS MODIFICADOS
- patient_routes.py → Regla PENDIENTE_SYNC
- consulta-hc.html → Mensaje de bloqueo
- registro-paciente.html → Bloqueo + generador datos
- carga-hc.html → Generador datos clínicos
- real_backend.py → sync_mode, outbox por nodo
- index.html → Sección Outbox por Nodo

## 🔌 ENDPOINTS CLAVE
- GET /api/dashboard/status
- GET /api/v1/patient/search/{doc}?sede=X
- POST /api/v1/patient/
- POST /api/v1/patient/import
- POST /api/clinical-records
- POST /api/sync/process-pending
- POST /api/nodes/{node}/fail|restore
- POST /api/cloud/fail|restore
- GET http://localhost:8080/fhir/metadata
- GET http://localhost:15672 (RabbitMQ)
