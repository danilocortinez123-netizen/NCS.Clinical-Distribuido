# 📸 Capturas de Pantalla — HIS Distribuido v3.0

Carpeta de evidencias visuales para el informe IEEE y la sustentación.

> **Instrucciones:** Toma las capturas con el sistema corriendo (`docker compose up -d`).  
> Guarda cada imagen con el nombre indicado en esta carpeta.

---

## Lista de capturas requeridas

| # | Nombre de archivo | Descripción | URL / Herramienta |
|---|---|---|---|
| 1 | `01_dashboard_command_center.png` | Dashboard principal con los 3 nodos ACTIVOS, KPIs, flujo arquitectural y tabla de eventos Outbox | `http://localhost:8001/` |
| 2 | `02_login_jwt.png` | Pantalla de login JWT — formulario con credenciales demo | `http://localhost:8001/login` |
| 3 | `03_registro_paciente.png` | Formulario de registro de paciente nuevo con todos los campos (demographics, EPS, municipio) | `http://localhost:8001/registro-paciente` |
| 4 | `04_triage_carga_hc.png` | Pantalla de Carga HC mostrando el bloque de **Triage** (selector sistema, nivel I-V, dolor, conciencia) y los signos vitales | `http://localhost:8001/carga-hc` |
| 5 | `05_consulta_importacion_cruzada.png` | Consulta de HC mostrando búsqueda de paciente remoto y botón de importación cross-sede | `http://localhost:8001/consulta-hc` |
| 6 | `06_detalle_paciente_timeline_fhir.png` | Detalle de paciente con timeline completo: Encounter, Observation, Condition, MedicationRequest | `http://localhost:8001/paciente/{id}` |
| 7 | `07_grafana_dashboard.png` | Dashboard Grafana "HIS Distribuido Overview" mostrando métricas Outbox por nodo y rates HTTP | `http://localhost:3000` |
| 8 | `08_prometheus_targets.png` | Prometheus targets — todos los 9 jobs en estado UP | `http://localhost:9090/targets` |
| 9 | `09_rabbitmq_management.png` | RabbitMQ Management UI — exchanges, queues, conexiones activas | `http://localhost:15672` |
| 10 | `10_hapi_fhir_metadata.png` | HAPI FHIR Capability Statement respondiendo JSON con `fhirVersion: 4.0.1` | `http://localhost:8080/fhir/metadata` |
| 11 | `11_simulacion_fallo_nodo.png` | Dashboard con Sincelejo marcado como **OFFLINE** (badge rojo) y banner de alerta activo | `http://localhost:8001/` → Simular caída Sincelejo |
| 12 | `12_outbox_pending_events.png` | Tabla de eventos Outbox con estados pending/processed/failed visibles | `http://localhost:8001/` → sección eventos |
| 13 | `13_docker_compose_ps.png` | Captura de terminal: `docker compose ps` — todos los contenedores en estado `Up` | Terminal |
| 14 | `14_postman_login_test.png` | Postman mostrando el request POST /auth/login con respuesta 200 y access_token | Postman |
| 15 | `15_postman_fhir_patient.png` | Postman mostrando GET FHIR Patient con datos del paciente sincronizado | Postman |

---

## Orden recomendado para tomar capturas

1. Levantar el sistema: `docker compose up -d`
2. Esperar 2-3 min para HAPI FHIR (JVM startup)
3. Login en `http://localhost:8001/login` → tomar captura 02
4. Registrar un paciente demo → tomar captura 03
5. Cargar HC con triage → tomar capturas 04
6. Ir al dashboard → tomar captura 01
7. Simular fallo de Sincelejo → tomar captura 11
8. Restaurar → tomar captura 12 (outbox events)
9. Abrir Grafana, Prometheus, RabbitMQ, HAPI FHIR → capturas 07-10
10. Terminal: `docker compose ps` → captura 13
11. Importar paciente cross-sede → capturas 05, 06
12. Postman: ejecutar login + FHIR → capturas 14, 15

---

## Notas técnicas

- Las capturas deben mostrar datos **reales** (no placeholder "—" en los KPIs)
- Para Grafana: configurar rango de tiempo a las últimas 15 minutos
- Para Prometheus: verificar que todos los targets están en estado UP (color verde)
- Para RabbitMQ: usuario `guest` / `guest`
- Para HAPI FHIR UI: `http://localhost:8080/`

---

*Esta carpeta es solo para evidencias. No subir imágenes personales ni datos reales de pacientes.*
