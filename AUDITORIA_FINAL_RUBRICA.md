# AUDITORÍA FINAL — HIS Distribuido vs. Rúbrica Sistemas Distribuidos
**Fecha:** 2026-05-25 · **Auditor:** Revisión automática estática de código  
**Rama analizada:** Working tree actual (sin commit final)

---

## RESUMEN EJECUTIVO

| Criterio | Estado |
|---|---|
| 1. Docker Compose | ✅ CUMPLE (parcial en healthchecks de microservicios) |
| 2. Tres nodos / ciudades | ⚠️ PARCIAL |
| 3. Base de datos distribuida | ⚠️ PARCIAL |
| 4. HAPI FHIR | ⚠️ PARCIAL |
| 5. Seguridad (JWT/OAuth2) | ⚠️ PARCIAL CRÍTICO |
| 6. Interfaces clínicas | ⚠️ PARCIAL |
| 7. Tolerancia a fallos | ⚠️ PARCIAL |
| 8. Observabilidad | ✅ CUMPLE |
| 9. GitHub | ⚠️ PARCIAL |
| 10. Informe IEEE | ❌ NO CUMPLE |

---

## TABLA DETALLADA

### 1. Docker Compose

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Servicios contenerizados | **CUMPLE** | 17 contenedores: gateway, patient, clinical, sync, rabbitmq, hapi-fhir, pg×3, prometheus, grafana, postgres-exporter×3 | — | — |
| Healthchecks | **PARCIAL** | RabbitMQ y pg_nodo1/2/3 tienen healthcheck; los 4 microservicios Python NO tienen healthcheck propio | Agregar healthcheck HTTP a gateway, patient, clinical, sync | ALTA |
| Restart policies | **CUMPLE** | Todos con `restart: unless-stopped` | — | — |
| Red interna | **CUMPLE** | Red `historia_clinica_net` (bridge) compartida | — | — |
| Volúmenes persistentes | **CUMPLE** | pg_data_nodo1/2/3, grafana_data como named volumes | RabbitMQ sin volumen (datos de colas efímeros) | BAJA |

---

### 2. Tres Nodos / Ciudades

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Sincelejo, Bogotá, Medellín nombrados | **CUMPLE** | `nodes_state` dict en real_backend.py; métricas Prometheus por ciudad; datos de demo en HTML | — | — |
| Nodos realmente independientes | **PARCIAL** | 3 PostgreSQL separados con sharding por documento_id. Pero 1 solo set de microservicios compartido. hybrid-deployment/ sí modela stacks independientes por ciudad | El compose principal no tiene servicios de aplicación por sede | MEDIA |
| Tráfico cruzado entre sedes | **PARCIAL** | patient_routes.py: búsqueda local → HAPI FHIR cloud si no encuentra. Import cross-sede via FHIR. sync_agent reenvía eventos locales → cloud RabbitMQ | No hay tráfico directo nodo-a-nodo; todo pasa por Cloud FHIR como hub | MEDIA |
| 3 HAPI FHIR o solo 1 Cloud Core | **PARCIAL** | 1 solo HAPI FHIR en compose principal. hybrid-deployment/cloud define HAPI cloud. Nodos locales sin HAPI propio | Arquitectura hub-and-spoke intencional, justificable en sustentación | MEDIA |

---

### 3. Base de Datos Distribuida

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Replicación real vs. nodos separados | **PARCIAL** | 3 PostgreSQL con sharding por documento_id (config.py L34-38). Sharding legítimo. Sin replicación WAL/streaming | Sin Patroni/Repmgr. Si cae pg_nodo1, datos de Sincelejo inaccessibles | ALTA |
| Consistencia eventual Outbox+HAPI | **CUMPLE** | outbox_poller.py: fetch_pending → publish RabbitMQ → handler FHIR → mark_published/failed. sync_agent con circuit-breaker real | — | — |
| Failover automático real | **NO CUMPLE** | nodes_state en real_backend.py son variables Python en memoria. No hay detección real de fallo de BD ni reconexión automática | Implementar try/catch en get_db_conn con fallback o degraded mode | ALTA |

---

### 4. HAPI FHIR

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| /metadata | **CUMPLE** | patient_routes.py L233: fhir_client.check_health() llama /metadata. Expuesto en /api/v1/patient/health/fhir | — | — |
| CRUD Patient | **CUMPLE** | POST /, GET /{id}, GET /search/{identifier}, POST /import con fhir_transformer FHIR R4 | — | — |
| CRUD Encounter | **CUMPLE** | POST /encounter → insert_encounter() + evento RabbitMQ → sync hacia HAPI | — | — |
| CRUD Observation | **CUMPLE** | POST /observation + signos vitales (PA, FC, FR, Temp, SpO2, Peso, Talla) en frontend | — | — |
| CRUD Condition | **CUMPLE** | POST /condition + CIE-10 en frontend | — | — |
| CRUD MedicationRequest | **CUMPLE** | clinical_handler procesa hacia FHIR. Frontend captura medicamento, vía, frecuencia, duración | — | — |
| Pruebas en 3 nodos | **PARCIAL** | test-mvp-fhir.sh existe pero prueba 1 solo endpoint HAPI | Falta demo: registrar Sincelejo → importar Bogotá → verificar Medellín. Falta colección Postman | ALTA |

---

### 5. Seguridad

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| JWT implementado (middleware) | **CUMPLE** | jwt_auth.py: middleware Bearer token completo, valida HS256, errores 401/403. PUBLIC_PATHS correctos | — | — |
| Endpoint login /auth/login | **NO CUMPLE** | PUBLIC_PATHS incluye /api/v1/auth/login pero el endpoint NO EXISTE en ningún router Python | Implementar POST /api/v1/auth/login con usuario/clave fijo demo y emisión de JWT | CRÍTICA |
| Frontend con login UI | **NO CUMPLE** | index.html no tiene pantalla de login. No hay formulario de auth | Agregar página login.html que llame /auth/login y guarde token | ALTA |
| OAuth2 | **NO CUMPLE** | No existe implementación OAuth2 | Trabajo futuro; JWT mínimo es suficiente para demo | BAJA |
| Secreto en config.py | **PARCIAL** | jwt_secret_key="super-secret-key-change-in-production" como default en config.py | Usar variable de entorno obligatoria sin default inseguro | MEDIA |
| .env no trackeado | **CUMPLE** | .env es untracked (git status: ??). No en historial git | Agregar `.env` literal (sin slash) al .gitignore | BAJA |

---

### 6. Interfaces Clínicas

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Admisión | **CUMPLE** | registro-paciente.html: 40+ campos (demográficos, EPS, municipio, motivo de consulta, antecedentes) | — | — |
| Triage con signos vitales y clasificación | **PARCIAL** | Clasificación triage I-V presente. Signos vitales en carga-hc.html (PA, FC, FR, Temp, SpO2, Peso, Talla) | NO es Manchester ni ESI explícito. Sin lógica automática de asignación de nivel por síntomas | MEDIA |
| Módulo médico CIE-10 y prescripción | **CUMPLE** | carga-hc.html: selector CIE-10 principal+secundario (10 códigos). Prescripción: medicamento, vía, frecuencia, duración, CUPS | Catálogo CIE-10 pequeño (demo aceptable) | — |
| Historia clínica consolidada | **CUMPLE** | detalle-paciente.html: timeline Encounter+Observation+Condition+MedicationRequest. consulta-hc.html | — | — |
| Reportes / Dashboard | **PARCIAL** | index.html: dashboard operacional (nodos, outbox, pacientes/sede). Link a Grafana | Sin reportes clínicos estadísticos (prevalencia diagnósticos, morbilidad) | BAJA |

---

### 7. Tolerancia a Fallos

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Caída de BD | **PARCIAL** | clinical_service consulta 3 nodos, continúa si uno falla. gateway apunta fijo a pg_nodo1 | Si cae pg_nodo1, gateway falla (outbox metrics, patients). Sin reconexión automática a nodo alt | ALTA |
| Caída de nodo (simulación) | **PARCIAL** | POST /nodes/{node_id}/fail cambia estado en memoria. POST /patients rechaza si sede OFFLINE | Es simulación visual: no mata contenedor ni bloquea BD real. Demostrable pero frágil | MEDIA |
| Caída de Cloud/HAPI | **PARCIAL** | POST /cloud/fail cambia cloud_state. Pacientes nuevos quedan PENDIENTE_SYNC. sync_agent circuit-breaker con threshold y reset configurable | Circuit breaker real para RabbitMQ→Cloud. Detección HAPI solo por timeout HTTP | MEDIA |
| Simulación vs. bloqueo real | **PARCIAL** | El sistema tiene 2 capas: simulación visual (vars en memoria) + comportamiento real (outbox, circuit breaker) | Demostrar ambas capas en sustentación | — |
| Resincronización automática | **CUMPLE** | OutboxPoller: ciclo cada 5s, procesa pendientes automáticamente. POST /sync/process-pending manual. sync_agent outbox retry | — | — |

---

### 8. Observabilidad

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Prometheus | **CUMPLE** | prom.yml: 9 jobs (prometheus, 4 microservicios, rabbitmq, 3 postgres exporters) | — | — |
| Grafana | **CUMPLE** | Provisioning automático. Dashboard his_overview.json con 8 panels (outbox totals, pending/failed by node, HTTP rates, RabbitMQ) | — | — |
| Métricas por nodo | **CUMPLE** | his_outbox_pending_by_node{node} y his_outbox_failed_by_node{node} con labels Sincelejo/Bogotá/Medellín | — | — |
| Métricas Outbox | **CUMPLE** | Gauges: pending_total, processed_total, failed_total, last_sync_timestamp. Actualización cada 10s | — | — |
| RabbitMQ exporter | **CUMPLE** | Plugin rabbitmq_prometheus habilitado. Puerto 15692 scrapeado | — | — |
| PostgreSQL exporters | **CUMPLE** | postgres-exporter-nodo1/2/3 con healthcheck dependency, puertos 9187/9188/9189 | — | — |
| FastAPI instrumentator | **CUMPLE** | Todos los microservicios con Instrumentator().instrument(app).expose(app, endpoint="/metrics") | — | — |

---

### 9. GitHub

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| README | **PARCIAL** | README.md (99 líneas): arquitectura, inicio rápido, servicios, endpoints, make commands | Falta: diagrama visual, capturas, instrucciones demo fallo, descripción ciudades | MEDIA |
| docker-compose.yml | **CUMPLE** | Presente en raíz, funcional | — | — |
| .env no trackeado | **CUMPLE** | .env es untracked (??). No en historial | Agregar .env literal al .gitignore | BAJA |
| .venv no trackeado | **CUMPLE** | .gitignore incluye .venv/ | — | — |
| .sql trackeados | **PARCIAL** | nodo1.sql, nodo2.sql, nodo3.sql SÍ están en git ls-files. .gitignore los excluye pero ya fueron commiteados | git rm --cached nodo1.sql nodo2.sql nodo3.sql + commit | ALTA |
| .bak no trackeados | **CUMPLE** | .gitignore excluye *.bak. .bak existentes son untracked | — | — |
| Logs no trackeados | **CUMPLE** | .gitignore excluye *.log | — | — |
| Secretos no trackeados | **CUMPLE** | .env con secrets no está trackeado | — | — |
| Colección Postman | **NO CUMPLE** | No existe ningún archivo .postman_collection.json | Crear colección con todos los endpoints | ALTA |
| Capturas de pantalla | **NO CUMPLE** | No existe ninguna imagen .png/.jpg en el repositorio | Crear docs/screenshots/ con: dashboard, triage, HC, Grafana, demo fallo | ALTA |
| backups .sql en repo | **PARCIAL** | backup_antes_deduplicacion.sql y backup_antes_limpieza.sql en raíz (46KB+31KB). .gitignore los excluye con backup_*.sql pero verificar si están trackeados | Confirmar con git ls-files. Si trackeados: git rm --cached | MEDIA |

---

### 10. Informe IEEE

| Criterio | Estado | Evidencia encontrada | Qué falta | Prioridad |
|---|---|---|---|---|
| Paper IEEE existe | **NO CUMPLE** | No existe ningún .pdf, .docx, .tex, paper* o *ieee* en el repositorio | Todo el paper IEEE por crear | CRÍTICA |
| Abstract inglés 150-250 palabras | **NO CUMPLE** | No existe | — | CRÍTICA |
| Keywords 4-6 | **NO CUMPLE** | No existe | — | CRÍTICA |
| Introducción | **NO CUMPLE** | No existe | — | CRÍTICA |
| Marco teórico | **NO CUMPLE** | No existe | — | CRÍTICA |
| Estado del arte | **NO CUMPLE** | No existe | — | CRÍTICA |
| Metodología / propuesta | **NO CUMPLE** | No existe | — | CRÍTICA |
| Resultados | **NO CUMPLE** | No existe | — | CRÍTICA |
| Discusión | **NO CUMPLE** | No existe | — | CRÍTICA |
| Conclusiones | **NO CUMPLE** | No existe | — | CRÍTICA |
| Referencias ≥8 recientes | **NO CUMPLE** | No existe | — | CRÍTICA |
| Máximo 7 páginas formato IEEE | **NO CUMPLE** | No existe | — | CRÍTICA |

---

## HALLAZGOS CRÍTICOS

### 🔴 CRÍTICO 1 — Endpoint /auth/login no implementado
JWT middleware activo y correcto, pero `/api/v1/auth/login` no existe como ruta Python.
El frontend no puede obtener tokens → todas las rutas protegidas retornan 401 en demo real.

### 🔴 CRÍTICO 2 — Paper IEEE completamente ausente
Representa una sección entera de la rúbrica sin ningún entregable.

### 🟡 IMPORTANTE 1 — .sql de schema trackeados en git
nodo1.sql, nodo2.sql, nodo3.sql presentes en `git ls-files`.

### 🟡 IMPORTANTE 2 — Sin capturas ni colección Postman
Evidencia visual y de prueba completamente ausentes del repositorio.

### 🟡 IMPORTANTE 3 — Arquitectura hub-and-spoke, no 3 nodos FHIR independientes
Justificable en sustentación como decisión de diseño consciente.
