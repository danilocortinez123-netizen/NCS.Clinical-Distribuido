# Historia Clínica Distribuida v3.0

Sistema de historia clínica distribuida con arquitectura de **microservicios**, interoperabilidad **FHIR R4** y fragmentación horizontal de datos.

## Arquitectura

```
gateway-service (:8000)  ← JWT Auth / Proxy
├── patient-service (:8002)  → HAPI FHIR (:8080)
├── clinical-service (:8003) → PostgreSQL x3 (sharded)
└── sync-service (:8004)     → RabbitMQ (event bus)
```

## Inicio Rápido

```bash
# Construir imágenes
docker compose build

# Levantar servicios
docker compose up -d

# Ver estado
docker compose ps

# Acceder
Gateway:     http://localhost:8000
HAPI FHIR:  http://localhost:8080/fhir
RabbitMQ:   http://localhost:15672 (guest/guest)
```

## Servicios

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| gateway-service | 8000 | API Gateway + Frontend |
| patient-service | 8002 | FHIR Patient CRUD |
| clinical-service | 8003 | Datos clínicos (sharded) |
| sync-service | 8004 | Event bus RabbitMQ |
| HAPI FHIR | 8080 | Servidor FHIR R4 |
| RabbitMQ | 5672/15672 | Mensajería |
| pg_nodo1 | 5433 | Shard 1 |
| pg_nodo2 | 5434 | Shard 2 |
| pg_nodo3 | 5435 | Shard 3 |

## Endpoints

### Gateway
- `GET /` - Dashboard
- `GET /health` - Health check

### Patient Service (via Gateway)
- `POST /api/v1/patient/` - Crear paciente
- `GET /api/v1/patient/{id}` - Obtener paciente
- `GET /api/v1/patient/search/{identifier}` - Buscar por documento
- `GET /api/v1/patient/health/fhir` - Estado HAPI FHIR

### Clinical Service (via Gateway)
- `POST /api/v1/clinical/encounter` - Crear atención
- `POST /api/v1/clinical/observation` - Crear observación
- `POST /api/v1/clinical/condition` - Crear diagnóstico
- `POST /api/v1/clinical/query` - Query SQL distribuida
- `GET /api/v1/clinical/nodes` - Estado de nodos

## Make Commands

```bash
make build    # Construir todo
make up       # Levantar servicios
make down     # Detener servicios
make logs     # Ver logs
make ps       # Estado
make clean    # Limpiar todo
```

## Documentación

- `docs/ARCHITECTURE.md` - Arquitectura detallada

## Estructura del Proyecto

```
├── services/
│   ├── gateway-service/   # API Gateway + JWT
│   ├── patient-service/   # FHIR Patient
│   ├── clinical-service/  # Datos clínicos sharded
│   └── sync-service/      # Event bus
├── frontend/              # Assets estáticos
├── database/              # SQL schemas
├── scripts/               # Utilidades
├── shared/                # Código compartido
├── docs/                  # Documentación
└── docker-compose.yml     # Orquestación
```

## Licencia

Proyecto educativo y de demostración.
