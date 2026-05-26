# 🏥 HIS Distribuido v3.0
## Sistema de Historia Clínica Distribuida — Proyecto Académico Sistemas Distribuidos

[![Docker](https://img.shields.io/badge/Docker-Compose-blue)](https://docs.docker.com/compose/)
[![FHIR](https://img.shields.io/badge/HL7-FHIR%20R4-orange)](https://hl7.org/fhir/R4/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)](https://www.postgresql.org/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3--management-orange)](https://www.rabbitmq.com/)

---

## 📋 Descripción

Sistema distribuido de historia clínica electrónica que implementa una arquitectura **hub-and-spoke** con 3 nodos geográficos (Sincelejo, Bogotá, Medellín) y un Cloud Core centralizado (HAPI FHIR R4 + RabbitMQ). Diseñado para demostrar conceptos clave de sistemas distribuidos:

- **Sharding horizontal** de PostgreSQL por sede geográfica
- **Consistencia eventual** mediante Outbox Pattern + RabbitMQ
- **Interoperabilidad HL7 FHIR R4** como formato de intercambio universal
- **Tolerancia a fallos** con circuit-breaker y resincronización automática
- **Observabilidad** completa con Prometheus + Grafana
- **Seguridad** con JWT HS256 en API Gateway

---

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CAPA DE PRESENTACIÓN                          │
│   Browser → http://localhost:8001                                     │
│   Login JWT  |  Dashboard  |  Registro  |  Carga HC  |  Consulta    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                    API GATEWAY (FastAPI :8000)                        │
│   JWT Auth Middleware  |  /api/v1/auth/login  |  Reverse Proxy       │
│   Métricas Prometheus  |  Dashboard Status    |  Nodos State         │
└──────┬────────────────┬──────────────────────┬────────────────────┘
       │                │                      │
┌──────▼──────┐  ┌──────▼──────┐  ┌───────────▼────────────┐
│ patient-    │  │ clinical-   │  │     sync-service        │
│ service     │  │ service     │  │  Outbox Poller          │
│ :8002       │  │ :8003       │  │  RabbitMQ Consumer      │
│ FHIR CRUD   │  │ 3-node shard│  │  HAPI FHIR Publisher    │
└──────┬──────┘  └──────┬──────┘  └───────────┬────────────┘
       │                │                      │
       │    ┌───────────┴──────────────────────┤
       │    │       PostgreSQL Shards          │
       │    │  pg_nodo1 (Sincelejo :5432)      │
       │    │  pg_nodo2 (Bogotá    :5433)      │
       │    │  pg_nodo3 (Medellín  :5434)      │
       │    └──────────────────────────────────┘
       │
       │    ┌──────────────────────────────────┐
       └───►│      CLOUD CORE                  │
            │  HAPI FHIR R4  :8080             │
            │  RabbitMQ      :5672 / :15672    │
            │  PostgreSQL cloud_pg             │
            └──────────────────────────────────┘

Observabilidad:
  Prometheus :9090  ←  9 scrapers (gateway, patient, clinical, sync,
                         rabbitmq, pg-exporter × 3, prometheus)
  Grafana    :3000  →  Dashboard "HIS Distribuido Overview"
```

---

## 🐳 Servicios Docker

| Servicio | Imagen / Build | Puerto | Función |
|---|---|---|---|
| `gateway-service` | FastAPI build | **8001** | API Gateway, JWT, Frontend, Métricas |
| `patient-service` | FastAPI build | 8002 | CRUD Pacientes, FHIR Client |
| `clinical-service` | FastAPI build | 8003 | HC, Sharding 3 nodos |
| `sync-service` | FastAPI build | 8004 | Outbox Poller, RabbitMQ Consumer |
| `hapi-fhir` | hapiproject/hapi | **8080** | FHIR R4 Cloud Core |
| `rabbitmq` | rabbitmq:3-management | 5672/15672 | Message Broker |
| `pg_nodo1` | postgres:16-alpine | 5432 | Shard Sincelejo |
| `pg_nodo2` | postgres:16-alpine | 5433 | Shard Bogotá |
| `pg_nodo3` | postgres:16-alpine | 5434 | Shard Medellín |
| `prometheus` | prom/prometheus | **9090** | Métricas / Scraping |
| `grafana` | grafana/grafana | **3000** | Dashboards |
| `postgres-exporter-nodo1/2/3` | wrouesnel/postgres_exporter | 9187-9189 | PostgreSQL → Prometheus |

---

## 🚀 Cómo ejecutar

### Prerrequisitos
- Docker Engine ≥ 24.x
- Docker Compose plugin ≥ 2.x
- 6 GB RAM libre (HAPI FHIR usa ~2 GB de JVM)
- Puertos libres: 8001, 8002, 8003, 8004, 8080, 5672, 15672, 9090, 3000

### Inicio rápido

```bash
# Clonar el repositorio
git clone <repo-url>
cd historia-clinica-distribuida

# Levantar todo (primera vez tarda ~3-5 min por descarga de imágenes y compilación JVM)
docker compose up -d

# Verificar estado
docker compose ps

# Ver logs
docker compose logs -f gateway-service
docker compose logs -f hapi-fhir
```

### Verificar que todo está corriendo

```bash
# Gateway (debe responder 200)
curl http://localhost:8001/health

# HAPI FHIR (puede tardar 2-3 min en estar listo)
curl http://localhost:8080/fhir/metadata | python3 -m json.tool | grep fhirVersion

# Métricas Outbox
curl -s http://localhost:8001/metrics | grep his_outbox
```

### Acceder al sistema

| Servicio | URL | Credenciales |
|---|---|---|
| 🏥 **Dashboard** | http://localhost:8001/ | admin / admin123 |
| 🔐 **Login** | http://localhost:8001/login | admin / admin123 |
| 📊 **Grafana** | http://localhost:3000/ | admin / admin |
| 📈 **Prometheus** | http://localhost:9090/ | — |
| 🐇 **RabbitMQ** | http://localhost:15672/ | guest / guest |
| 🌐 **HAPI FHIR** | http://localhost:8080/ | — |
| 📖 **API Docs** | http://localhost:8001/docs | — |

---

## 👤 Usuarios de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Administrador del sistema |
| `medico` | `medico123` | Médico tratante |
| `enfermera` | `enfermera123` | Personal de enfermería |

---

## 🎬 Flujo de demostración (15 minutos)

### 1. Registro de paciente (Sincelejo)
1. Abrir http://localhost:8001/ → redirige a login
2. Ingresar con `admin / admin123`
3. Dashboard: verificar 3 nodos ACTIVOS y HAPI FHIR conectado
4. Ir a **Registro Paciente** → seleccionar sede **Sincelejo**
5. Llenar datos del paciente → Guardar → el KPI de Sincelejo incrementa

### 2. Carga de Historia Clínica con Triage
1. Ir a **Carga Historia Clínica**
2. Buscar el paciente registrado por cédula
3. Llenar bloque de **Triage**: sistema Colombia 5 niveles, signos vitales
4. Clic en **Sugerir Nivel de Triage** → algoritmo automático asigna nivel
5. Llenar Encounter, CIE-10, prescripción → **Guardar y Sincronizar**

### 3. Interoperabilidad cross-sede (Bogotá importa de Sincelejo)
1. Ir a **Consulta HC** → seleccionar sede **Bogotá**
2. Buscar el paciente de Sincelejo → aparece como "remoto"
3. Clic en **Importar desde HAPI FHIR** → el paciente y su HC aparecen en Bogotá
4. Ir al detalle del paciente → timeline completo con Encounter, Observations, Conditions

### 4. Simulación de tolerancia a fallos
1. En el Dashboard → Panel Simulación → **Caída Sincelejo**
2. Intentar crear paciente en Sincelejo → error controlado (nodo offline)
3. Crear paciente en Bogotá → funciona sin problema
4. Dashboard: eventos de Sincelejo quedan en **PENDING** en el Outbox
5. **Restaurar Todo** → Outbox poller reenvía automáticamente en 5 segundos
6. Verificar en Grafana: métricas de pending bajaron a 0

---

## 📡 Endpoints principales

### Autenticación
```
POST /api/v1/auth/login       # { username, password } → { access_token }
```

### Sistema
```
GET  /health                  # Estado del gateway
GET  /api/dashboard/status    # KPIs: pacientes por sede, outbox totals, nodes state
GET  /metrics                 # Prometheus metrics
```

### Pacientes
```
POST /api/v1/patient/                    # Crear paciente
GET  /api/v1/patient/search/{documento}  # Buscar por cédula
GET  /api/v1/patient/{id}               # Obtener por ID
POST /api/v1/patient/import             # Importar cross-sede desde FHIR
GET  /api/v1/patient/health/fhir        # Estado conexión HAPI FHIR
```

### Historia Clínica
```
POST /api/clinical-records                      # Registrar HC completa
POST /api/v1/clinical/encounter                 # Solo Encounter
GET  /api/v1/clinical/health/distributed        # Estado 3 nodos BD
```

### Administración
```
POST /api/v1/admin/outbox/process-pending       # Procesar outbox manualmente
GET  /api/v1/admin/dashboard/recent-events      # Eventos recientes
```

### Control de nodos (demo)
```
POST /api/nodes/{sede}/fail     # Simular caída de nodo
POST /api/nodes/{sede}/restore  # Restaurar nodo
POST /api/cloud/fail            # Simular caída Cloud FHIR
POST /api/cloud/restore         # Restaurar Cloud
GET  /api/nodes/status          # Estado de todos los nodos
```

### HAPI FHIR (directo :8080)
```
GET  /fhir/metadata             # Capability Statement R4
GET  /fhir/Patient              # Todos los pacientes
GET  /fhir/Patient/{id}         # Por ID
GET  /fhir/Encounter?_summary=count
GET  /fhir/Observation?_summary=count
GET  /fhir/Condition?_summary=count
GET  /fhir/MedicationRequest?_summary=count
```

---

## 📊 Observabilidad

### Prometheus
- URL: http://localhost:9090
- 9 scrapers configurados: gateway, patient, clinical, sync, rabbitmq, pg-exporter×3, prometheus
- Métricas custom `his_outbox_*` con labels por nodo

### Grafana
- URL: http://localhost:3000 (admin/admin)
- Dashboard "HIS Distribuido Overview" auto-provisionado con:
  - Outbox: pending/processed/failed totals
  - Pending by node (Sincelejo/Bogotá/Medellín)
  - HTTP Request rate por servicio
  - RabbitMQ queue metrics

### Métricas personalizadas (gateway)
```
his_outbox_pending_total          # Total eventos pendientes
his_outbox_processed_total        # Total procesados
his_outbox_failed_total           # Total fallidos
his_outbox_pending_by_node{node}  # Pendientes por sede
his_outbox_failed_by_node{node}   # Fallidos por sede
his_outbox_last_sync_timestamp    # Último sync exitoso (epoch)
```

---

## 🔄 Outbox Pattern — Consistencia Eventual

El sistema implementa el **Transactional Outbox Pattern** para garantizar consistencia eventual entre los nodos locales y el Cloud FHIR:

```
Operación clínica
      │
      ▼
INSERT en tabla local (historia_clinica) ─┐
INSERT en event_outbox (status=pending)   │  ← Transacción atómica
      │                                   │
      ▼
OutboxPoller (cada 5s)
      │
      ├─ Cloud disponible?
      │      ├─ SÍ → publish to RabbitMQ → SyncService → HAPI FHIR
      │      │           → mark status=processed
      │      └─ NO → mantiene status=pending → retry en 5s
      │
      └─ CircuitBreaker: si 3 fallos consecutivos → OPEN 30s → no intenta
```

**Garantías:**
- At-least-once delivery (idempotency check via event_id)
- Persistencia de eventos aunque el proceso reinicie
- Métricas observables en Prometheus/Grafana

---

## ⚡ Tolerancia a Fallos

### Caída de nodo local (shards BD)
- Clinical service ejecuta queries en los 3 nodos; si uno falla, continúa con los demás
- Los eventos del nodo caído quedan en `event_outbox` con status=pending
- Al restaurar el nodo, el OutboxPoller reenvía automáticamente

### Caída del Cloud FHIR / RabbitMQ
- El sync_agent implementa un **circuit-breaker real** (`circuit_breaker.py`):
  - `CLOSED` (normal): forward inmediato
  - `OPEN` (3 fallos): espera 30s sin intentar
  - `HALF-OPEN`: intenta 1 request de prueba
- Los eventos quedan en `sync_agent_outbox` y se reintentan automáticamente

### Simulación de fallos (demo)
El endpoint `POST /api/nodes/{sede}/fail` simula el fallo a nivel lógico (plano de datos) sin detener contenedores, ideal para demostración en tiempo real. El outbox real sigue funcionando en background.

---

## 🔒 Seguridad

- **JWT HS256** en todos los endpoints protegidos
- `JWTAuthMiddleware` en el API Gateway intercepta todas las rutas
- Rutas públicas: `/login`, `/health`, `/metrics`, `/api/v1/auth/login`
- Token expira en **8 horas**

> ⚠️ Las credenciales en este repositorio son exclusivamente para **demo académico**. En producción usar OAuth2/OpenID Connect (Keycloak, Auth0) y variables de entorno seguras.

---

## ⚠️ Limitaciones documentadas (Trabajo Futuro)

| Limitación | Justificación de Diseño | Trabajo Futuro |
|---|---|---|
| **1 HAPI FHIR Cloud Core** (no 3 instancias FHIR) | Arquitectura hub-and-spoke intencional: estándar en redes de salud colombianas (similar a RNEC como repositorio central). Los nodos locales tienen autonomía operativa. | Federación FHIR: 3 servidores FHIR con replicación bi-direccional |
| **Sharding por sede** (no replicación WAL) | El sharding horizontal por rango de documento_id es estrategia legítima de distribución. La consistencia entre nodos se delega al Outbox + HAPI FHIR como fuente de verdad. | PostgreSQL Patroni/Repmgr para réplicas con failover automático |
| **Simulación visual de fallos** (no detención real de contenedor) | La simulación de plano lógico es controlada y reproducible para demo. El comportamiento real (circuit-breaker, outbox retry) opera en paralelo. | Integración con Docker API para detención real de contenedores |
| **OAuth2 incompleto** | JWT HS256 provee autenticación suficiente para demo académico. OAuth2 requeriría un IdP externo (Keycloak). | Keycloak + PKCE + roles clínicos RBAC |
| **Catálogo CIE-10 limitado** | 10 códigos frecuentes suficientes para demostración. | Integración con base de datos CIE-10 completa (71,000+ códigos) |

---

## 📁 Estructura del proyecto

```
historia-clinica-distribuida/
├── docker-compose.yml           # Orquestación principal (17 servicios)
├── .env.example                 # Variables de entorno de referencia
├── Makefile                     # Comandos útiles
├── database/                    # Schemas SQL de inicialización
│   ├── nodo_schema.sql
│   └── events/init-events.sh
├── frontend/
│   └── templates/               # HTML pages
│       ├── login.html           # Página de autenticación JWT
│       ├── index.html           # Dashboard Command Center
│       ├── registro-paciente.html
│       ├── carga-hc.html        # HC + Triage 5 niveles
│       ├── consulta-hc.html
│       └── detalle-paciente.html
├── services/
│   ├── gateway_service/         # API Gateway + JWT + Frontend Server
│   ├── patient_service/         # CRUD Pacientes + FHIR Client
│   ├── clinical_service/        # Historia Clínica + Sharding 3 nodos
│   ├── sync_service/            # Outbox Poller + RabbitMQ Consumer
│   └── sync_agent/              # Bridge Local → Cloud (circuit-breaker)
├── hybrid-deployment/           # Compose para despliegue multi-host real
│   ├── docker-compose.cloud.yml # Stack Cloud (HAPI FHIR, RabbitMQ cloud)
│   └── docker-compose.local.yml # Stack Local por sede
├── docs/
│   ├── ARCHITECTURE.md
│   ├── paper_ieee.md            # Paper IEEE formato académico
│   ├── HIS_Distribuido.postman_collection.json
│   └── screenshots/             # Evidencias visuales
└── monitoring/                  # Prometheus + Grafana config
    ├── prometheus/prom.yml
    └── grafana/dashboards/his_overview.json
```

---

## 🛠️ Makefile — Comandos útiles

```bash
make up          # docker compose up -d
make down        # docker compose down (sin borrar volúmenes)
make logs        # logs de todos los servicios
make status      # docker compose ps
make rebuild     # forzar reconstrucción de imágenes
make fhir-check  # curl del FHIR /metadata
make metrics     # curl de /metrics del gateway
```

---

## 📚 Referencias técnicas

- [HL7 FHIR R4 Specification](https://hl7.org/fhir/R4/)
- [HAPI FHIR Server](https://hapifhir.io/)
- [Transactional Outbox Pattern](https://microservices.io/patterns/data/transactional-outbox.html)
- [CAP Theorem — Brewer 2000](https://dl.acm.org/doi/10.1145/343477.343502)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Prometheus Monitoring](https://prometheus.io/docs/)
- [Grafana Dashboards](https://grafana.com/docs/)
- [Manual Triage Colombia MSPS](https://www.minsalud.gov.co/)

---

*Proyecto académico — Sistemas Distribuidos 2026 | Universidad de Sucre*
