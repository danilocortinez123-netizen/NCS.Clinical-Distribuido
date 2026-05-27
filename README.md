# NCS Clinical

## Sistema Clínico Distribuido para Registro, Consulta y Sincronización de Historias Clínicas

NCS Clinical es un proyecto académico de sistemas distribuidos enfocado en la gestión de información clínica entre diferentes sedes. El sistema permite iniciar sesión, registrar pacientes, cargar historias clínicas, consultar información médica, visualizar métricas, revisar eventos Outbox y simular fallos de nodos.

---

## Descripción general

El sistema trabaja con tres sedes principales:

- Sincelejo
- Bogotá
- Medellín

Cada sede permite registrar pacientes y asociarlos a historias clínicas. El dashboard muestra pacientes por ciudad, eventos procesados, eventos pendientes, eventos fallidos y estado de los nodos.

---

## Funcionalidades principales

- Login de acceso al sistema.
- Dashboard principal con métricas.
- Registro de pacientes por sede.
- Verificación de paciente antes del registro.
- Carga de historia clínica.
- Consulta de historia clínica.
- Eventos Outbox recientes.
- Simulación de caída de nodos.
- Restauración de nodos.
- Procesamiento de eventos pendientes.
- Monitoreo con Grafana.
- Mensajería con RabbitMQ.
- Integración con HAPI FHIR.

---

## Usuarios de demostración

| Usuario | Contraseña | Rol |
|---|---|---|
| admin | admin123 | Administrador |
| medico | medico123 | Médico |

---

## Cómo ejecutar el proyecto

```bash
git clone https://github.com/danilocortinez123-netizen/NCS.Clinical-Distribuido.git
cd NCS.Clinical-Distribuido
docker compose up -d --build

Autor
Danilo Diaz-Brayan Portacio
Proyecto académico desarrollado para la asignatura de Sistemas Distribuidos.
