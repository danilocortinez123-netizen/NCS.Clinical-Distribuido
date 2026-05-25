# Arquitectura - Historia Clínica Distribuida v3.0

## Visión General

Sistema de historia clínica distribuida basado en **microservicios** con orientación a **eventos**, interoperabilidad **FHIR R4** y fragmentación horizontal (**sharding**) de datos clínicos en PostgreSQL.

## Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────┐
│                           CLIENTE                                   │
│                    (Browser / Postman / App)                        │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     ╔═══════════════════════╗                       │
│                     ║   API GATEWAY :8000   ║  ← JWT Auth          │
│                     ║   FastAPI             ║  ← Route Proxy       │
│                     ╚═══════════╦═══════════╝                       │
│                                 │                                   │
│                 ┌───────────────┼───────────────┐                   │
│                 ▼               ▼               ▼                   │
│        ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│        │  PATIENT   │  │  CLINICAL  │  │   SYNC     │  Events      │
│        │  :8002     │  │  :8003     │  │  :8004     │──────┐      │
│        └─────┬──────┘  └─────┬──────┘  └─────┬──────┘      │      │
│              │               │               │             │      │
├──────────────┼───────────────┼───────────────┼─────────────┼──────┤
│              ▼               ▼               ▼             ▼      │
│   ┌──────────────┐  ┌────────────────┐  ┌──────────┐ ┌──────────┐│
│   │ HAPI FHIR    │  │ PostgreSQL x3  │  │ RabbitMQ │ │ Audit    ││
│   │ :8080        │  │ (sharded)      │  │ :5672    │ │ Logs     ││
│   │ FHIR R4      │  │ 5433/5434/5435 │  │ Events   │ │          ││
│   └──────────────┘  └────────────────┘  └──────────┘ └──────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## Microservicios

### 1. gateway-service (:8000)
- **API Gateway** con autenticación JWT
- Enruta peticiones a patient-service y clinical-service
- Sirve frontend estático (HTML/JS/CSS)
- Middleware de validación de tokens

### 2. patient-service (:8002)
- CRUD de recursos FHIR Patient
- Transformación de datos colombianos → FHIR R4 (fhir.resources)
- Conexión con HAPI FHIR Server
- 15 campos de identificación del paciente (MinSalud Colombia)

### 3. clinical-service (:8003)
- CRUD de datos clínicos: Encounter, Observation, Condition, Discharge
- Conexión directa a los 3 nodos PostgreSQL fragmentados
- Fragmentación horizontal por `documento_id`
- Repositorio distribuido con enrutamiento automático

### 4. sync-service (:8004)
- **Event Bus** vía RabbitMQ (topic exchange)
- Publica eventos cuando ocurren cambios
- Consume eventos para auditoría y replicación
- Tipos: `patient.created`, `patient.updated`, `clinical.encounter.created`,
  `clinical.observation.created`, `clinical.condition.created`

## Sharding (Fragmentación)

| Nodo | Puerto | Rango documento_id |
|------|--------|-------------------|
| pg_nodo1 | 5433 | < 4,000,000,000 |
| pg_nodo2 | 5434 | 4,000,000,000 - 6,999,999,999 |
| pg_nodo3 | 5435 | ≥ 7,000,000,000 |

## Flujo de Eventos

```
Patient Creado → EventBus → Audit Log
                          → Notificación
                          → Replicación (futuro)

Encounter Creado → EventBus → Audit Log
                           → Sincronización FHIR
```

## Stack Tecnológico

| Componente | Tecnología |
|-----------|-----------|
| Lenguaje | Python 3.11 |
| API Framework | FastAPI + Uvicorn |
| API Gateway | FastAPI (custom) |
| Autenticación | JWT (PyJWT) |
| FHIR Server | HAPI FHIR (hapiproject/hapi) |
| FHIR SDK | fhir.resources 7.1 |
| Base de Datos | PostgreSQL 15 (sharded) |
| Mensajería | RabbitMQ 3 (aio-pika) |
| Frontend | HTML/JS Vanilla + Phosphor Icons |
| Contenedores | Docker + Docker Compose |

## Seguridad

- JWT Bearer Token en gateway
- Middleware de autenticación en gateway-service
- Red interna Docker para comunicación entre servicios
- CORS configurado para desarrollo

## Próximas Mejoras

- [ ] Kubernetes manifests (k8s/)
- [ ] Service Discovery (Consul/K8s)
- [ ] API Rate Limiting
- [ ] OpenTelemetry tracing
- [ ] Health checks + Circuit Breaker
- [ ] Frontend React/Vue
- [ ] CI/CD pipeline
