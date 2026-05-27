cd ~/NCS.Clinical-Distribuido

cat > README.md <<'EOF'
# NCS Clinical

## Sistema Clínico Distribuido para Registro, Consulta y Sincronización de Historias Clínicas

NCS Clinical es un proyecto académico de sistemas distribuidos enfocado en la gestión de información clínica entre diferentes sedes. El sistema permite iniciar sesión, registrar pacientes, cargar historias clínicas, consultar información médica, visualizar métricas, revisar eventos Outbox y simular fallos de nodos para demostrar tolerancia a fallos y sincronización.

---

## Descripción general

El sistema trabaja con tres sedes principales:

- Sincelejo
- Bogotá
- Medellín

Cada sede permite registrar pacientes y asociarlos a historias clínicas. El dashboard muestra los pacientes por ciudad, eventos procesados, eventos pendientes, eventos fallidos y estado de los nodos.

El proyecto utiliza una arquitectura distribuida con servicios independientes, bases de datos PostgreSQL, mensajería con RabbitMQ, monitoreo con Grafana y Prometheus, y sincronización clínica usando recursos FHIR.

---

## Funcionalidades principales

- Login de acceso al sistema.
- Dashboard principal con métricas del sistema.
- Registro de pacientes por sede.
- Verificación de paciente antes del registro.
- Carga de historia clínica.
- Consulta de historia clínica.
- Visualización de eventos Outbox.
- Simulación de caída de nodos.
- Restauración de nodos.
- Procesamiento de eventos pendientes.
- Monitoreo con Grafana.
- Mensajería con RabbitMQ.
- Integración con HAPI FHIR.

---

## Arquitectura del sistema

```text
Usuario
  |
  v
Frontend NCS Clinical
  |
  v
API Gateway
  |
  +--> Servicio de Pacientes
  |
  +--> Servicio Clínico
  |
  +--> Servicio de Sincronización
  |
  +--> RabbitMQ
  |
  +--> HAPI FHIR
  |
  +--> PostgreSQL por nodos
          |
          +--> Nodo Sincelejo
          +--> Nodo Bogotá
          +--> Nodo Medellín
Servicios principales
Servicio	Puerto	Función
Gateway / Frontend	8001	Entrada principal del sistema
Patient Service	8002	Gestión de pacientes
Clinical Service	8003	Gestión de historias clínicas
Sync Service	8004	Sincronización y eventos
HAPI FHIR	8080	Servidor FHIR
RabbitMQ	15672	Panel de mensajería
Grafana	3000	Panel de métricas
Prometheus	9090	Recolección de métricas
PostgreSQL Nodo 1	5432	Base Sincelejo
PostgreSQL Nodo 2	5433	Base Bogotá
PostgreSQL Nodo 3	5434	Base Medellín
Usuarios de demostración
Usuario	Contraseña	Rol
admin	admin123	Administrador
medico	medico123	Médico
Cómo ejecutar el proyecto
git clone https://github.com/danilocortinez123-netizen/NCS.Clinical-Distribuido.git
cd NCS.Clinical-Distribuido
docker compose up -d --build

Verificar contenedores:

docker ps

Ver logs del gateway:

docker compose logs -f gateway-service
Acceso al sistema
Módulo	URL	Credenciales
Login	http://localhost:8001/login	admin / admin123
Dashboard	http://localhost:8001	admin / admin123
RabbitMQ	http://localhost:15672	guest / guest
Grafana	http://localhost:3000	admin / admin
Prometheus	http://localhost:9090	Sin credenciales
HAPI FHIR	http://localhost:8080	Sin credenciales
Flujo de uso
Iniciar sesión en NCS Clinical.
Entrar al dashboard principal.
Registrar un paciente seleccionando la sede.
Verificar que el contador de pacientes cambie en el dashboard.
Cargar historia clínica del paciente.
Consultar la historia clínica registrada.
Revisar eventos Outbox recientes.
Simular caída de Sincelejo, Bogotá, Medellín o Cloud.
Restaurar los nodos.
Procesar eventos pendientes.
Dashboard

El dashboard permite visualizar:

Pacientes registrados en Sincelejo.
Pacientes registrados en Bogotá.
Pacientes registrados en Medellín.
Pacientes sincronizados en base de datos.
Pacientes enviados a Cloud FHIR.
Estado de nodos.
Eventos Outbox recientes.
Panel de simulación y control.
Registro de pacientes

El módulo de registro permite:

Seleccionar tipo de documento.
Buscar si el paciente ya existe.
Registrar datos personales.
Seleccionar sede.
Guardar el paciente.
Actualizar automáticamente los contadores del dashboard.
Carga de historia clínica

El módulo de carga HC permite registrar información clínica del paciente, incluyendo:

Datos de atención médica.
Datos de triaje.
Diagnóstico.
Fórmula médica.
Observaciones clínicas.
Generación de eventos clínicos.
Consulta de historia clínica

El módulo de consulta HC permite buscar pacientes registrados y revisar la información clínica almacenada. Cuando el paciente tiene historia clínica, se visualizan los recursos clínicos asociados.

Eventos Outbox

El sistema usa eventos Outbox para controlar la sincronización.

Estados principales:

Estado	Significado
processed	Evento procesado correctamente
pending	Evento pendiente por procesar
failed	Evento con error
Simulación de fallos

NCS Clinical permite simular fallos de nodos desde el dashboard:

Caída Sincelejo.
Caída Bogotá.
Caída Medellín.
Caída Cloud.
Restaurar todo.
Procesar eventos pendientes.

Esto permite demostrar tolerancia a fallos y recuperación del sistema.

Estructura del proyecto
NCS.Clinical-Distribuido/
├── docker-compose.yml
├── README.md
├── database/
├── frontend/
│   ├── static/
│   └── templates/
│       ├── login.html
│       ├── index.html
│       ├── registro-paciente.html
│       ├── carga-hc.html
│       ├── consulta-hc.html
│       └── detalle-paciente.html
├── services/
│   ├── gateway_service/
│   ├── patient_service/
│   ├── clinical_service/
│   └── sync_service/
└── monitoring/
    ├── prometheus/
    └── grafana/
Comandos útiles

Levantar el sistema:

docker compose up -d --build

Apagar el sistema:

docker compose down

Ver contenedores:

docker ps

Ver logs:

docker compose logs -f

Reiniciar gateway:

docker compose restart gateway-service
Tecnologías utilizadas
Docker
Docker Compose
FastAPI
PostgreSQL
RabbitMQ
HAPI FHIR
Prometheus
Grafana
HTML
CSS
JavaScript
JWT
Objetivo académico

El objetivo de NCS Clinical es demostrar el funcionamiento de una solución clínica distribuida, aplicando conceptos como comunicación entre servicios, sincronización de eventos, monitoreo, tolerancia a fallos y gestión de datos clínicos por sedes.

Autor
Danilo Diaz-Brayan Portacio
Proyecto académico desarrollado para la asignatura de Sistemas Distribuidos.

n
