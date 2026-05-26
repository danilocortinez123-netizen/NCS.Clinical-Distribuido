# PLAN FINAL DE ENTREGA — HIS Distribuido
**Generado:** 2026-05-25 | **Basado en:** AUDITORIA_FINAL_RUBRICA.md

---

## 1. LO QUE FALTA IMPLEMENTAR SÍ O SÍ

Estos ítems son bloqueantes para la entrega o la demo. Sin ellos el proyecto no puede defenderse.

### 🔴 CRÍTICO — Sin excusa

| # | Qué falta | Dónde | Esfuerzo estimado |
|---|---|---|---|
| C1 | **Endpoint POST /api/v1/auth/login** — emite JWT con usuario/clave hardcodeados para demo | `services/gateway_service/app/routes/real_backend.py` | 1-2 horas |
| C2 | **Pantalla de login en frontend** — formulario simple que llama /auth/login y guarda token en localStorage | `frontend/templates/login.html` o sección en index.html | 1-2 horas |
| C3 | **Paper IEEE** — 7 páginas máximo en formato IEEE, secciones completas | Nuevo archivo `docs/paper_ieee.md` o `docs/paper_ieee.pdf` | 6-12 horas |
| C4 | **Capturas de pantalla** — mínimo 5: dashboard, registro, carga HC, Grafana, demo fallo | Carpeta `docs/screenshots/` | 30 min (tomar screenshots corriendo) |
| C5 | **Colección Postman** — todos los endpoints del sistema | Nuevo archivo `docs/HIS_Distribuido.postman_collection.json` | 2-3 horas |

### 🟡 IMPORTANTE — Limpieza git antes de entrega

| # | Qué falta | Comando | Esfuerzo |
|---|---|---|---|
| L1 | Quitar .sql de schema del tracking git | `git rm --cached nodo1.sql nodo2.sql nodo3.sql` | 5 min |
| L2 | Agregar `.env` literal al .gitignore (sin slash) | Editar `.gitignore`, agregar línea `.env` | 2 min |
| L3 | Healthchecks para microservicios Python en docker-compose.yml | 4 bloques healthcheck con curl /health | 15 min |
| L4 | Commit final limpio con mensaje descriptivo | `git add -A && git commit -m "feat: versión final HIS Distribuido v3.0"` | 5 min |

---

## 2. LO QUE SE PUEDE JUSTIFICAR EN SUSTENTACIÓN

Estos ítems son "PARCIAL" pero tienen argumentación técnica sólida. Prepara la explicación.

### 🟡 Arquitectura hub-and-spoke (1 HAPI FHIR, no 3)
**Argumento:** El modelo adoptado es intencionalmente **híbrido**: 3 nodos locales (PostgreSQL shards) + 1 Cloud FHIR Core como broker de interoperabilidad. Este patrón es estándar en redes de salud reales (ej. Colombia: cada IPS tiene su sistema local + RNEC como repositorio central). La consistencia eventual se logra via Outbox Pattern + RabbitMQ, lo cual es arquitecturalmente más robusto que 3 instancias FHIR independientes sin coordinación.

### 🟡 Simulación de fallos visual vs. real
**Argumento:** La simulación de `POST /nodes/{id}/fail` es una abstracción de control del plano de datos. En producción, el estado de los nodos se detectaría via health endpoints o timeouts. El sistema SÍ tiene comportamiento real: el outbox funciona aunque el flag sea "visual", el circuit-breaker de sync_agent es código real con thresholds configurables.

### 🟡 Triage I-V sin escala Manchester/ESI
**Argumento:** El sistema implementa clasificación por niveles de urgencia (I=Inmediato, II=Emergencia, III=Urgente, IV=Menos Urgente, V=No Urgente), que es la clasificación del Manual para la Clasificación del Triage del MSPS Colombia (5 niveles), equivalente funcional a Manchester y ESI. No se llama "Manchester" pero aplica los mismos principios de priorización.

### 🟡 Sin replicación PostgreSQL real
**Argumento:** El sharding horizontal por rango de `documento_id` es una estrategia legítima de distribución de datos. La replicación entre nodos se delegó al Outbox Pattern + HAPI FHIR como single source of truth. El sistema privilegia disponibilidad y consistencia eventual (CAP: AP) sobre consistencia fuerte, lo cual es el estándar en sistemas de salud distribuidos geográficamente.

### 🟡 Resincronización "manual" para la demo
**Argumento:** La resincronización automática existe (OutboxPoller, sync_agent). El botón manual de `POST /sync/process-pending` es para control explícito en demo, no porque no exista automatismo.

### 🟡 Nodos sin stacks de microservicio independientes
**Argumento:** El `hybrid-deployment/` contiene la arquitectura de despliegue real por sede (`docker-compose.local.yml` replicable por ciudad + `docker-compose.cloud.yml`). El `docker-compose.yml` principal es para demostración local all-in-one, que es lo apropiado para un entorno de desarrollo/evaluación.

---

## 3. LO QUE SE PUEDE DEJAR COMO TRABAJO FUTURO

Sin impacto en la nota si se menciona explícitamente en el paper o en la sustentación.

| Ítem | Justificación como trabajo futuro |
|---|---|
| OAuth2 / OpenID Connect | Integración con IdP (Keycloak, Auth0) para SSO multi-sede |
| Replicación PostgreSQL streaming (Patroni/Repmgr) | Alta disponibilidad con failover automático real |
| 3 instancias HAPI FHIR independientes (federadas) | Federación FHIR con replicación entre servidores |
| Reportes clínicos estadísticos (prevalencia, morbilidad) | Módulo de BI/analytics sobre datos clínicos |
| Alertas automáticas en Grafana (PagerDuty) | Notificaciones proactivas de fallo de nodo |
| HTTPS/TLS entre microservicios | mTLS para comunicación segura intra-red |
| RBAC por rol (médico, enfermera, admin) | Control de acceso basado en roles clínicos |
| Tests automatizados (pytest + CI/CD) | Pipeline de calidad automático |
| Catálogo CIE-10 completo (>71,000 códigos) | Busqueda y autocompletado de diagnósticos |
| Lógica automática de triage Manchester | Algoritmo que asigne nivel según síntomas |

---

## 4. ORDEN RECOMENDADO PARA TERMINAR

**Tiempo disponible estimado necesario: 12-18 horas de trabajo concentrado**

### FASE 1 — Lo que desbloquea la demo (4 horas)
```
Hora 0-1: Implementar POST /api/v1/auth/login en real_backend.py
Hora 1-2: Agregar página de login en frontend
Hora 2-3: Tomar capturas de pantalla del sistema corriendo
Hora 3-4: Limpiar git (rm --cached .sql, .gitignore, commit)
```

### FASE 2 — Evidencia de prueba (3 horas)
```
Hora 4-5: Crear colección Postman básica (10 endpoints clave)
Hora 5-6: Agregar healthchecks a docker-compose.yml para microservicios
Hora 6-7: Mejorar README con diagrama ASCII/Mermaid y capturas
```

### FASE 3 — Paper IEEE (6-10 horas, puede ir en paralelo)
```
Usar RESUMEN_IMPLEMENTACION.md, ARCHITECTURE.md, MVP_FHIR_IMPLEMENTADO.md como base
Estructura: Abstract → Intro → Marco teórico → Estado del arte → Metodología → Resultados → Conclusiones → Referencias
Redactar en LaTeX IEEE template o Word IEEE template
Mínimo 8 referencias: FHIR R4 spec, CAP theorem, Outbox pattern, HL7 v2 vs FHIR, sistemas distribuidos Colombia
```

### FASE 4 — Pulido final (1 hora)
```
Verificar que docker compose up --build funciona limpio
Ejecutar test-mvp-fhir.sh y documentar output
Commit final con tag v3.0
```

---

## 5. COMANDOS DE VERIFICACIÓN

### Docker Compose
```bash
# Levantar todo limpio
docker compose down -v
docker compose up -d --build

# Verificar todos los servicios running
docker compose ps

# Verificar healthchecks
docker inspect pg_nodo1 | grep -A5 '"Health"'
docker inspect pg_nodo2 | grep -A5 '"Health"'
docker inspect pg_nodo3 | grep -A5 '"Health"'
docker inspect rabbitmq | grep -A5 '"Health"'
```

### HAPI FHIR — Verificar endpoints
```bash
# Metadata (debe responder con fhirVersion: 4.0.1)
curl http://localhost:8080/fhir/metadata | python3 -m json.tool | grep fhirVersion

# Contar Patients
curl http://localhost:8080/fhir/Patient?_summary=count

# Contar Encounters
curl http://localhost:8080/fhir/Encounter?_summary=count

# Contar Observations
curl http://localhost:8080/fhir/Observation?_summary=count

# Contar Conditions
curl http://localhost:8080/fhir/Condition?_summary=count

# Contar MedicationRequests
curl http://localhost:8080/fhir/MedicationRequest?_summary=count
```

### JWT Auth (una vez implementado)
```bash
# Obtener token
TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Usar token en llamada protegida
curl -H "Authorization: Bearer $TOKEN" http://localhost:8001/api/patients
```

### Verificar 3 nodos PostgreSQL
```bash
# Nodo 1 (Sincelejo)
docker exec -it pg_nodo1 psql -U admin -d historia_clinica -c "SELECT COUNT(*) FROM patients WHERE sede='Sincelejo';"

# Nodo 2 (Bogotá)
docker exec -it pg_nodo2 psql -U admin -d historia_clinica -c "SELECT COUNT(*) FROM patients WHERE sede='Bogotá';"

# Nodo 3 (Medellín)
docker exec -it pg_nodo3 psql -U admin -d historia_clinica -c "SELECT COUNT(*) FROM patients WHERE sede='Medellín';"

# Outbox events
docker exec -it pg_nodo1 psql -U admin -d historia_clinica -c "SELECT LOWER(status), COUNT(*) FROM event_outbox GROUP BY 1;"
```

### Observabilidad
```bash
# Prometheus targets
curl -s http://localhost:9090/api/v1/targets | python3 -m json.tool | grep '"health"'

# Métricas Outbox
curl -s http://localhost:8001/metrics | grep his_outbox

# RabbitMQ status
curl -s http://localhost:15672/api/overview -u guest:guest | python3 -m json.tool
```

### Git limpieza
```bash
# Verificar qué .sql están trackeados
git ls-files | grep "\.sql$"

# Remover del tracking
git rm --cached nodo1.sql nodo2.sql nodo3.sql 2>/dev/null || true

# Verificar .env no trackeado
git ls-files | grep "^\.env$"

# Ver estado limpio
git status --short
```

### Ejecutar test existente
```bash
chmod +x test-mvp-fhir.sh
./test-mvp-fhir.sh
```

---

## 6. CHECKLIST DE DEMO DE 15 MINUTOS

### Prep (antes de iniciar — 5 min previos)
- [ ] `docker compose up -d --build` ejecutado y todos los servicios `Up`
- [ ] HAPI FHIR respondiendo: `curl http://localhost:8080/fhir/metadata`
- [ ] Abrir en browser: Dashboard (localhost:8001), Grafana (localhost:3000)
- [ ] Tener datos pre-cargados en los 3 nodos

---

### Demo en vivo (15 minutos)

**Min 0-2: Arquitectura (hablar mientras muestran el dashboard)**
- [ ] Abrir `http://localhost:8001` → mostrar dashboard principal
- [ ] Señalar: 3 nodos (Sincelejo/Bogotá/Medellín) ACTIVOS
- [ ] Señalar: Cloud HAPI FHIR ACTIVO
- [ ] Señalar: Eventos Outbox (pending/processed)

**Min 2-4: Registro de paciente en Sincelejo**
- [ ] Ir a "Nuevo Paciente" → seleccionar sede Sincelejo
- [ ] Llenar campos con datos de prueba (o usar botón de ejemplo)
- [ ] Guardar → mostrar mensaje de sincronización
- [ ] Regresar al dashboard → el contador de Sincelejo aumentó

**Min 4-7: Flujo clínico completo**
- [ ] Ir a "Carga de HC" → buscar paciente recién creado
- [ ] Llenar: motivo de consulta, signos vitales (PA, FC, FR, Temp, SpO2)
- [ ] Seleccionar CIE-10 (ej. J06.9 - Infección respiratoria)
- [ ] Agregar prescripción: medicamento, vía, frecuencia
- [ ] Guardar → mostrar que se envió evento al outbox

**Min 7-9: Interoperabilidad cross-sede**
- [ ] Ir a Bogotá → buscar el paciente de Sincelejo por cédula
- [ ] Mostrar que aparece como "remoto" / "requiere importación"
- [ ] Importar → aparece con historia clínica completa
- [ ] Señalar: datos vinieron de HAPI FHIR (cloud)

**Min 9-11: Tolerancia a fallos**
- [ ] En dashboard: clic en "Simular fallo" de Sincelejo
- [ ] Intentar crear paciente en Sincelejo → error controlado
- [ ] Crear paciente en Bogotá → funciona (nodo independiente)
- [ ] Mostrar outbox: los eventos de Sincelejo quedan en "pending"
- [ ] Restaurar Sincelejo → `POST /sync/process-pending` → eventos se procesan

**Min 11-13: Observabilidad**
- [ ] Abrir Grafana (localhost:3000, admin/admin)
- [ ] Mostrar dashboard "HIS Distribuido - Overview"
- [ ] Señalar: pending/processed/failed totals
- [ ] Señalar: pending by node (Sincelejo/Bogotá/Medellín)
- [ ] Señalar: HTTP requests del gateway
- [ ] Abrir Prometheus (localhost:9090) → targets → todos UP

**Min 13-15: Cierre**
- [ ] Mostrar `docker compose ps` → todos los servicios running
- [ ] Mencionar: 17 contenedores, red interna, volúmenes persistentes
- [ ] Mencionar: Outbox Pattern + RabbitMQ para consistencia eventual
- [ ] Mencionar: Circuit breaker para resiliencia cloud

---

### Preguntas frecuentes preparadas

**P: ¿Por qué solo 1 HAPI FHIR y no 3?**
R: Arquitectura hub-and-spoke intencionalmente, estándar en redes de salud colombianas. Los nodos locales tienen autonomía operativa y la nube centraliza la interoperabilidad.

**P: ¿Cómo garantizan consistencia si HAPI cae?**
R: Outbox Pattern. Los eventos quedan en la tabla `event_outbox` con status=pending. El OutboxPoller los reintenta cada 5 segundos. El sync_agent tiene circuit-breaker para no saturar el sistema.

**P: ¿El fallo de nodo es real o simulado?**
R: Doble capa: la simulación visual controla el plano lógico, el outbox/circuit-breaker es código real que funciona independientemente. En producción, la detección de fallo sería via health endpoints.

**P: ¿Qué protocolo de seguridad usan?**
R: JWT HS256 en el API Gateway. El middleware intercepta todas las rutas no públicas y valida el Bearer token antes de pasar la solicitud al microservicio destino.
