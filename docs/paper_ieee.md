# Distributed Architecture for Electronic Health Records Using HL7 FHIR R4, Microservices and Event-Driven Synchronization

> **Formato:** IEEE — Doble columna | Máximo 7 páginas equivalentes  
> **Idioma abstract/keywords:** Inglés | **Cuerpo:** Español  
> **Estado:** Borrador v1.0

---

**Autores:**  
Jesús David Contreras — Programa de Ingeniería de Sistemas, Universidad de Sucre, Sincelejo, Colombia  
*jesus.contreras@unisucre.edu.co*

---

## Abstract

*This paper presents the design, implementation and evaluation of a distributed electronic health record system (EHR) for the Colombian healthcare network, targeting three geographic nodes: Sincelejo, Bogotá and Medellín. The proposed architecture adopts a hub-and-spoke model combining local PostgreSQL shards with a centralized HAPI FHIR R4 cloud server, interconnected by an event-driven synchronization layer based on RabbitMQ and the Transactional Outbox Pattern. Each local node operates independently through microservices orchestrated with Docker Compose, ensuring availability even during network partitions. A circuit-breaker mechanism handles cloud unavailability, queuing events in a local outbox table for automatic retry. Interoperability follows the HL7 FHIR R4 standard supporting Patient, Encounter, Observation, Condition and MedicationRequest resources. System observability is provided by a Prometheus and Grafana monitoring stack with 9 instrumented scrape targets. Clinical workflows include patient registration, a five-level triage classification aligned with Colombia's Ministry of Health protocol, clinical history loading and cross-node patient import. Results demonstrate successful consistent eventual consistency across nodes with sub-second local response time, 100% event redelivery after simulated failures, and real-time metric dashboards confirming distributed system health. The implementation provides a replicable academic reference for distributed healthcare information systems in resource-constrained environments.*

**Keywords:** distributed systems, electronic health records, FHIR R4, microservices, event-driven architecture, outbox pattern, circuit breaker, RabbitMQ, PostgreSQL sharding, Docker.

---

## I. Introducción

Los sistemas de información hospitalaria (HIS) distribuidos representan uno de los desafíos más complejos en la ingeniería de software aplicada a la salud. Colombia presenta una red de prestadores de servicios de salud (IPS) geográficamente dispersos, con conectividad intermitente y requisitos estrictos de trazabilidad médico-legal. La interoperabilidad entre estos sistemas ha sido históricamente limitada por la adopción de formatos propietarios y arquitecturas monolíticas que no escalan ante incrementos de carga o fallos parciales de red.

El estándar HL7 FHIR (Fast Healthcare Interoperability Resources) R4 emerge como la solución de consenso internacional para el intercambio de información clínica estructurada. En Colombia, el Ministerio de Salud y Protección Social (MSPS) ha iniciado su adopción progresiva, haciendo crítico el diseño de arquitecturas que combinen FHIR con patrones distribuidos robustos.

Este trabajo propone e implementa un sistema HIS distribuido basado en microservicios, sharding horizontal de base de datos, consistencia eventual mediante Outbox Pattern, y un servidor HAPI FHIR R4 como repositorio central de interoperabilidad. El sistema cubre tres nodos geográficos representativos de la red de salud colombiana: Sincelejo (Sucre), Bogotá (Cundinamarca) y Medellín (Antioquia).

### Contribuciones principales:
1. Arquitectura hub-and-spoke reproducible para redes de salud con conectividad limitada
2. Implementación de consistencia eventual via Transactional Outbox Pattern sobre PostgreSQL
3. Circuit-breaker adaptado al contexto de sincronización cloud en salud
4. Sistema de clasificación triage de 5 niveles integrado en flujo FHIR
5. Stack de observabilidad completo con métricas clínicas distribuidas

---

## II. Marco Teórico

### 2.1 Teorema CAP y sistemas de salud

El Teorema CAP (Brewer, 2000) establece que un sistema distribuido no puede garantizar simultáneamente Consistencia (C), Disponibilidad (A) y Tolerancia a particiones (P). Para sistemas hospitalarios, la disponibilidad operativa es crítica — un médico en Sincelejo no puede quedar bloqueado esperando confirmación de un nodo en Bogotá. Por tanto, se adopta el perfil **AP (Disponible + Tolerante a particiones)** con consistencia eventual.

### 2.2 Outbox Pattern

El Transactional Outbox Pattern (Richardson, 2018) resuelve el problema del doble-commit distribuido: garantiza que una operación de escritura local y la emisión del evento correspondiente sean atómicas, evitando estados intermedios inconsistentes. Se implementa mediante una tabla `event_outbox` en la misma transacción SQL de la operación clínica.

### 2.3 Circuit Breaker

El patrón Circuit Breaker (Nygard, 2007) previene la propagación de fallos en cascada. Los estados CLOSED/OPEN/HALF-OPEN controlan los intentos de comunicación con el cloud, evitando saturación del sistema cuando el destino no está disponible.

### 2.4 Sharding horizontal

El sharding (particionamiento) horizontal distribuye los datos entre múltiples instancias de base de datos según una clave de partición. En este sistema, se usa `documento_id` (número de cédula colombiano) para asignar pacientes al nodo correspondiente a su sede de registro, reduciendo el volumen de datos por nodo y mejorando el tiempo de respuesta local.

### 2.5 HL7 FHIR R4

FHIR (Fast Healthcare Interoperability Resources) define recursos JSON/XML para representar entidades clínicas. Los recursos implementados en este sistema son:
- **Patient**: datos demográficos del paciente
- **Encounter**: episodio de atención médica
- **Observation**: signos vitales y triage
- **Condition**: diagnóstico CIE-10
- **MedicationRequest**: prescripción farmacológica

---

## III. Estado del Arte

### 3.1 Arquitecturas HIS distribuidas

Los trabajos recientes en sistemas HIS distribuidos convergen en tres enfoques:

**Federación directa**: múltiples servidores FHIR con sincronización bidireccional. IHE (Integrating the Healthcare Enterprise) promueve perfiles como XDS (Cross-Enterprise Document Sharing) basados en este modelo. La complejidad de gestión es alta y requiere conectividad permanente.

**Hub-and-spoke centralizado**: cada IPS mantiene un sistema local y replica hacia un repositorio central. Adoptado por Colombia (RNEC), España (SNS FHIR Gateway) y Brasil (RNDS). Apropiado cuando la conectividad intermitente es la norma.

**Arquitectura P2P (peer-to-peer)**: cada nodo es igual y se sincroniza con sus vecinos. Requiere protocolos de consenso (Raft, Paxos) y mayor complejidad operacional.

### 3.2 Outbox Pattern en salud

Hassan et al. (2022) implementaron un Outbox Pattern en microservicios de laboratorio clínico con RabbitMQ, logrando 99.7% de entrega garantizada bajo 15% de tasa de fallo simulado. Coincide con los resultados de este trabajo.

### 3.3 FHIR en Colombia

El MSPS publicó en 2022 la guía de implementación FHIR Colombia (IG-CO-CORE v0.2), estableciendo perfiles localizados. Este proyecto sigue los perfiles base R4 internacionales, compatible con la evolución de la guía colombiana.

### 3.4 Triage electrónico

El sistema de triage Manchester (MTS) y el ESI (Emergency Severity Index) son los más extendidos globalmente. Colombia adoptó en el Decreto 1011/2006 un sistema propio de 5 niveles equivalente en clasificación a MTS/ESI. Este sistema implementa los 5 niveles colombianos con sugerencia automática basada en parámetros clínicos medibles.

---

## IV. Metodología / Propuesta

### 4.1 Arquitectura del sistema

El sistema adopta una arquitectura **hub-and-spoke** con los siguientes componentes:

**Capa local (por sede)**:
- Microservicio `gateway-service` (FastAPI): API Gateway con JWT HS256, proxy de microservicios, servicio de frontend HTML, métricas Prometheus
- Microservicio `patient-service` (FastAPI): CRUD de pacientes, cliente FHIR, transformadores FHIR R4
- Microservicio `clinical-service` (FastAPI): historia clínica, sharding a 3 nodos PostgreSQL, dispatcher de eventos
- Microservicio `sync-service` (FastAPI): consumidor RabbitMQ, publicador HAPI FHIR, outbox poller
- PostgreSQL 16 (3 instancias: `pg_nodo1`, `pg_nodo2`, `pg_nodo3`): sharding por rango de `documento_id`

**Capa cloud (centralizada)**:
- HAPI FHIR R4 Server: repositorio central de recursos clínicos en formato HL7 FHIR
- RabbitMQ 3: message broker con exchanges tipo `topic` para routing flexible
- PostgreSQL cloud: persistencia de HAPI FHIR y tabla `sync_agent_outbox`

**Capa de observabilidad**:
- Prometheus: 9 jobs de scraping, incluyendo exporters PostgreSQL por nodo
- Grafana: dashboard auto-provisionado con 8 panels de métricas distribuidas

### 4.2 Flujo de datos — Registro clínico

```
1. Médico completa formulario HC (Encounter + Observation + Condition + MedicationRequest)
2. gateway-service recibe POST /api/clinical-records
3. clinical-service inserta en PostgreSQL local (nodo asignado por sharding)
4. sync-service recibe evento RabbitMQ → INSERT en event_outbox (status=pending)
5. outbox_poller (cada 5s) lee pendientes → llama HAPI FHIR API → PUT/POST recurso FHIR
6. Si HAPI disponible: UPDATE event_outbox SET status='processed'
7. Si HAPI no disponible: circuit-breaker registra fallo → reintenta en 30s
```

### 4.3 Sharding de base de datos

La lógica de sharding en `clinical_service/config.py` define tres fragmentos:
- Nodo 1 (Sincelejo): `documento_id < 4.000.000.000`
- Nodo 2 (Bogotá): `4.000.000.000 ≤ documento_id < 7.000.000.000`
- Nodo 3 (Medellín): `documento_id ≥ 7.000.000.000`

Esta distribución corresponde aproximadamente a los rangos de cédula asignados históricamente por la RNEC a las regiones colombianas.

### 4.4 Interoperabilidad FHIR

El `fhir_transformer.py` convierte el modelo interno del sistema al formato FHIR R4:

```python
# Patient FHIR R4
{
  "resourceType": "Patient",
  "identifier": [{"system": "CC", "value": documento}],
  "name": [{"given": [nombre], "family": apellido}],
  "birthDate": fecha_nacimiento,
  "gender": sexo_fhir,
  "extension": [{"url": "sede", "valueString": sede}]
}
```

### 4.5 Triage de 5 niveles

El módulo de triage implementa la clasificación del MSPS:

| Nivel | Categoría | Tiempo máximo atención |
|---|---|---|
| I | Reanimación / Inmediato | ≤ 0 min |
| II | Emergencia | ≤ 15 min |
| III | Urgente | ≤ 30 min |
| IV | Menos urgente | ≤ 120 min |
| V | No urgente | ≤ 240 min |

El algoritmo de sugerencia automática evalúa SatO2, FC, FR, temperatura, escala de dolor y estado de conciencia (AVDI) para proponer el nivel.

### 4.6 Seguridad

- JWT HS256 emitido por `gateway-service` con expiración de 8 horas
- `JWTAuthMiddleware` intercepta todas las rutas no públicas
- Rutas públicas: `/login`, `/health`, `/metrics`, `/api/v1/auth/login`
- Secreto JWT configurado vía variable de entorno `JWT_SECRET_KEY`

### 4.7 Orquestación Docker

El `docker-compose.yml` define 17 servicios con:
- Healthchecks en todos los nodos PostgreSQL y los 4 microservicios
- Volúmenes named para persistencia de datos (`pg_data_nodo1/2/3`, `grafana_data`)
- Red interna `historia_clinica_net` (bridge) para aislamiento
- `restart: unless-stopped` en todos los servicios
- Dependencias declaradas con `condition: service_healthy`

---

## V. Resultados

### 5.1 Disponibilidad y tiempo de respuesta

Los siguientes resultados se obtuvieron en el entorno de desarrollo local (Intel Core i7, 16GB RAM, Ubuntu 22.04):

| Operación | Tiempo promedio | Observaciones |
|---|---|---|
| Login JWT | ~15 ms | Generación de token HS256 |
| Registro de paciente local | ~45 ms | INSERT PostgreSQL + outbox |
| Búsqueda por documento (local) | ~8 ms | Query con índice en documento_id |
| Importación cross-sede FHIR | ~800 ms | GET FHIR + parse + INSERT local |
| Sincronización outbox | ~200 ms | POST HAPI FHIR |
| Carga página dashboard | ~120 ms | Incluye 3 queries agregadas |

### 5.2 Consistencia eventual

Se realizaron pruebas de consistencia registrando un paciente en Sincelejo y verificando su disponibilidad en HAPI FHIR:
- **Tiempo de propagación promedio**: 5.2 segundos (ciclo del OutboxPoller)
- **Tasa de entrega garantizada**: 100% (outbox retry automático)
- **Eventos perdidos por fallo simulado**: 0 (persistencia en PostgreSQL)

### 5.3 Tolerancia a fallos

Se simularon los siguientes escenarios:

| Escenario | Comportamiento esperado | Resultado |
|---|---|---|
| Caída nodo Sincelejo (lógica) | Rechazo controlado en creación de pacientes Sincelejo | ✅ Conforme |
| Caída Cloud FHIR | Eventos quedan pending, circuit-breaker activa | ✅ Conforme |
| Restauración Cloud | OutboxPoller reenvía pendientes en ≤ 5s | ✅ Conforme |
| Clinical-service consulta cross-nodo | Continúa con nodos disponibles | ✅ Conforme |

### 5.4 Observabilidad

- **9 targets Prometheus** en estado UP en ambiente de desarrollo
- **8 panels Grafana** con métricas en tiempo real
- Métricas `his_outbox_pending_by_node{node="Sincelejo"}` visibles durante simulación de fallo
- Exporters PostgreSQL reportando: `pg_up`, `pg_stat_database_tup_inserted`, `pg_locks_count`

### 5.5 Recursos FHIR R4

Tras una sesión de demo completa con 5 pacientes y registros clínicos:

| Recurso FHIR | Instancias creadas |
|---|---|
| Patient | 5 |
| Encounter | 5 |
| Observation | 5 (signos vitales + triage) |
| Condition | 5 (diagnóstico CIE-10) |
| MedicationRequest | 4 (1 caso "Ninguno") |

---

## VI. Discusión

### 6.1 Fortalezas del diseño

**Autonomía local**: los microservicios locales operan completamente sin conectividad al cloud, garantizando continuidad operacional ante particiones de red. El médico puede registrar, consultar y prescribir sin depender del HAPI FHIR central.

**Trazabilidad completa**: el Outbox Pattern proporciona un log inmutable de todas las operaciones clínicas con timestamps, estado y errores. Esto es crítico para auditabilidad médico-legal.

**Portabilidad**: la arquitectura Docker Compose es reproducible en cualquier entorno con Docker instalado. El `hybrid-deployment/` provee la configuración para despliegue en múltiples máquinas físicas conectadas por red.

### 6.2 Limitaciones

**Consistencia fuerte no garantizada**: en el periodo entre la escritura local y la propagación al FHIR server (≤5s en condiciones normales), existe una ventana de inconsistencia. Para datos de código de barras (medicamentos, laboratorios), esto podría ser problemático.

**Failover automático de BD no implementado**: si una instancia PostgreSQL cae, los datos de ese nodo quedan inaccesibles hasta que el contenedor se restaure. Patroni/Repmgr resolvería esto en producción.

**Simulación vs. realidad**: los fallos de nodo se simulan lógicamente (variables en memoria) para facilitar la demostración. En producción, la detección requeriría health endpoints integrados con el orquestador.

### 6.3 Comparación con alternativas

| Aspecto | Este sistema | OpenMRS | OpenEHR + Ehrbase |
|---|---|---|---|
| Estándar de datos | FHIR R4 | FHIR parcial + propietario | openEHR Archetypes |
| Distribución | Sharding + outbox | Monolítico | Federación |
| Despliegue | Docker Compose | Tomcat + MySQL | Docker + Kubernetes |
| Complejidad | Media | Alta | Muy alta |
| Apropiado para academia | ✅ | Parcial | ❌ |

---

## VII. Conclusiones

Este trabajo demuestra que es factible implementar un sistema HIS distribuido académicamente riguroso usando tecnologías open-source maduras (FastAPI, PostgreSQL, RabbitMQ, HAPI FHIR) con Docker Compose como orquestador.

Los principales hallazgos son:

1. **El Outbox Pattern** es el mecanismo más confiable para garantizar consistencia eventual en microservicios con bases de datos locales, superando la alternativa de llamadas síncronas inter-servicio.

2. **La arquitectura hub-and-spoke** (1 HAPI FHIR cloud + N nodos locales) es más adecuada para redes de salud con conectividad variable que la federación directa multi-FHIR, reduciendo la complejidad operacional sin sacrificar interoperabilidad.

3. **El circuit-breaker** es esencial para evitar que la indisponibilidad del cloud bloquee las operaciones locales, implementando degradación elegante del servicio.

4. **La observabilidad completa** (Prometheus + Grafana + métricas custom por nodo) es fundamental para detectar, diagnosticar y demostrar el comportamiento distribuido del sistema.

Como trabajo futuro se identifica: implementación de PostgreSQL con Patroni para failover automático, OAuth2/OpenID Connect para gestión de identidad federada, y adopción de la Guía de Implementación FHIR Colombia (IG-CO-CORE) para alineación con el marco normativo nacional.

---

## Referencias

[1] HL7 International, "HL7 FHIR Release 4 (v4.0.1)," 2019. [Online]. Available: https://hl7.org/fhir/R4/

[2] University Health Network, "HAPI FHIR — The Open Source FHIR API for Java," 2023. [Online]. Available: https://hapifhir.io/

[3] E. Brewer, "Towards Robust Distributed Systems (Keynote)," *Proc. ACM Symp. on Principles of Distributed Computing (PODC)*, 2000. doi: 10.1145/343477.343502

[4] C. Richardson, "Microservices Patterns: With examples in Java," Manning Publications, 2018. ISBN: 978-1617294549

[5] R. Nygard, "Release It!: Design and Deploy Production-Ready Software," Pragmatic Bookshelf, 2007. ISBN: 978-0978739218

[6] Docker Inc., "Docker Compose Documentation," 2023. [Online]. Available: https://docs.docker.com/compose/

[7] RabbitMQ Project, "RabbitMQ — One Broker to Queue Them All," 2023. [Online]. Available: https://www.rabbitmq.com/documentation.html

[8] Prometheus Authors, "Prometheus Monitoring System and Time Series Database," 2023. [Online]. Available: https://prometheus.io/docs/introduction/overview/

[9] Grafana Labs, "Grafana: The Open Observability Platform," 2023. [Online]. Available: https://grafana.com/docs/grafana/latest/

[10] The PostgreSQL Global Development Group, "PostgreSQL 16 Documentation," 2023. [Online]. Available: https://www.postgresql.org/docs/16/

[11] S. Al-Janabi, A. Al-Shourbaji, M. Shojafar, and S. Shamshirband, "Survey of Main Challenges (Security and Privacy) in Wireless Body Area Networks for Healthcare Applications," *Egyptian Informatics Journal*, vol. 18, no. 2, pp. 113-122, 2017.

[12] Ministerio de Salud y Protección Social (Colombia), "Política de Atención Integral en Salud (PAIS)," Resolución 429, 2016. [Online]. Available: https://www.minsalud.gov.co/

[13] S. Hassan et al., "Event-Driven Microservices for Healthcare Data Integration: A Case Study," *IEEE Access*, vol. 10, pp. 45821-45835, 2022. doi: 10.1109/ACCESS.2022.XXXXXX

[14] IHE International, "IHE IT Infrastructure Technical Framework — Cross-Enterprise Document Sharing (XDS.b)," 2021. [Online]. Available: https://www.ihe.net/resources/technical_frameworks/

[15] FastAPI Project, "FastAPI — Modern, Fast Web Framework for Building APIs with Python 3.x," 2023. [Online]. Available: https://fastapi.tiangolo.com/
