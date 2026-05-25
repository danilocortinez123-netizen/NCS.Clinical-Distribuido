# CHECKLIST DEMO — HIS Distribuido v3.0
Flujo completo para sustentación académica

---

## PASO 1 — Levantar sistema
```bash
cd ~/historia-clinica-distribuida
docker compose up -d --build
```
Esperar ~30s. Verificar en: http://localhost:8001

---

## PASO 2 — Registrar paciente en Sincelejo
1. Ir a http://localhost:8001/registro-paciente
2. Verificar que la sede activa es **Sincelejo**
3. Clic en **"🧪 Datos de Prueba"** → Se llena automáticamente
4. Clic en **"Guardar Localmente"** (NO "Guardar y Sincronizar")
5. ✅ Resultado: Paciente creado con sync_status = PENDIENTE_SYNC
6. ✅ El evento queda en event_outbox con status = pending

**LO QUE EXPLICAS**: "El paciente se guardó localmente en el nodo Sincelejo. 
El Outbox Pattern asegura que el evento se registra atómicamente."

---

## PASO 3 — Ver pendiente por nodo en Dashboard
1. Ir a http://localhost:8001
2. Ver sección **"Estado Outbox por Nodo"**
3. ✅ Sincelejo muestra Pendientes: 1
4. ✅ El banner dice "Hay eventos pendientes en: Sincelejo"
5. ✅ En "Eventos Outbox Recientes" aparece el evento patient.created con badge pending

---

## PASO 4 — Intentar importar desde Bogotá (DEBE BLOQUEARSE)
1. Ir a http://localhost:8001/consulta-hc
2. Cambiar sede activa a **Bogotá**
3. Buscar el documento del paciente recién registrado
4. ✅ RESULTADO ESPERADO: Aparece panel amarillo de advertencia
5. ✅ Mensaje: "Paciente no disponible en la red. Está pendiente de sincronización..."
6. ✅ NO aparece botón de importar

**LO QUE EXPLICAS**: "La consistencia eventual exige que el paciente se sincronice 
con el Cloud Core antes de ser visible en otras sedes. Esto previene duplicados."

---

## PASO 5 — Procesar pendientes (sincronizar con FHIR)
1. Ir al Dashboard http://localhost:8001
2. Clic en **"🔄 Procesar Eventos Pendientes"**
3. ✅ Modal muestra: "Se procesarán: 1 evento de Sincelejo"
4. Confirmar
5. ✅ Toast: "Eventos procesados y sincronizados"
6. ✅ Dashboard actualiza: Pendientes → 0, Procesados → N

---

## PASO 6 — Ver paciente en Cloud FHIR
1. Ir a http://localhost:8080/fhir/Patient (puede tardar si HAPI no tuvo tiempo)
2. O usar: http://localhost:8001/api/dashboard/status → ver cloud_fhir_patients
3. ✅ Paciente visible en HAPI FHIR

---

## PASO 7 — Importar desde Bogotá (AHORA SÍ FUNCIONA)
1. Ir a http://localhost:8001/consulta-hc
2. Sede activa: **Bogotá**
3. Buscar el documento
4. ✅ Ahora aparece: "Paciente encontrado en otra sede / Cloud Core"
5. Clic **"Importar a Bogotá"**
6. ✅ Paciente importado con sync_status = IMPORTED_FROM_REMOTE

---

## PASO 8 — Cargar Historia Clínica con generador
1. Ir a http://localhost:8001/carga-hc
2. Sede activa: **Bogotá**
3. Buscar el documento del paciente importado
4. Clic **"🧪 Datos de Prueba"** → Se llena el formulario
5. Clic **"Guardar y Sincronizar"**
6. ✅ Toast de éxito
7. ✅ Evento ClinicalRecordCreated → processed en outbox

---

## PASO 9 — Ver detalle con FHIR JSON
1. Ir a http://localhost:8001/consulta-hc
2. Buscar paciente → Clic en "Ver Detalle"
3. ✅ Línea de tiempo muestra la carga clínica
4. ✅ Diagnóstico CIE-10 visible
5. ✅ Botón "Ver Contenido FHIR" muestra JSON real
6. Ver también sección "Mapeo FHIR R4": Patient, Encounter, Condition, MedicationRequest

---

## PASO 10 — Simular caída Cloud
1. En Dashboard, clic **"🌩️ Caída Cloud"**
2. ✅ Modal explicativo: "Simulación lógica para sustentación"
3. Confirmar
4. ✅ Estado Cloud → Offline (badge rojo)
5. Ir a Registro → Crear paciente → Guardar Localmente
6. ✅ sync_status = PENDIENTE_SYNC (cloud estaba caído)
7. ✅ Evento en outbox = pending

**LO QUE EXPLICAS**: "El sistema es tolerante a fallos. Si el cloud cae, 
los nodos continúan operando localmente y acumulan eventos en el Outbox."

---

## PASO 11 — Restaurar Cloud y resincronizar
1. En Dashboard, clic **"✅ Restaurar Todo"**
2. ✅ Estado Cloud → Activo (badge verde)
3. Clic **"Procesar Eventos Pendientes"**
4. ✅ Los eventos pendientes se sincronizan
5. ✅ Dashboard muestra Pendientes → 0

**LO QUE EXPLICAS**: "Al restaurar la conectividad, el sistema automáticamente 
puede procesar todos los eventos acumulados durante el fallo."

---

## ENDPOINTS RÁPIDOS PARA MOSTRAR EN DEMO
- Dashboard API: http://localhost:8001/api/dashboard/status
- Pacientes: http://localhost:8001/api/patients
- FHIR Metadata: http://localhost:8080/fhir/metadata
- FHIR Pacientes: http://localhost:8080/fhir/Patient
- RabbitMQ: http://localhost:15672 (guest/guest)
- Swagger Gateway: http://localhost:8001/docs
- Swagger Patients: http://localhost:8002/docs
- Swagger Sync: http://localhost:8004/docs

---

## FRASES CLAVE PARA SUSTENTACIÓN
- "Implementamos el **Outbox Pattern** para garantizar consistencia entre el estado local y el cloud"
- "La **sincronización eventual** permite que los nodos operen independientemente durante fallos"
- "Los datos clínicos son transformados a **FHIR R4** para interoperabilidad estándar"
- "El **sharding por sede** distribuye la carga entre los 3 nodos PostgreSQL"
- "El **Gateway Service** centraliza la seguridad JWT y el enrutamiento"

---

## PASO 12 — Observabilidad (Prometheus y Grafana)
1. En el Dashboard principal, clic en **"📊 Ver Grafana"** o ir a http://localhost:3000
2. Iniciar sesión con `admin` / `admin`
3. Ir a Dashboards -> "HIS Distribuido - Overview"
4. ✅ Mostrar panel "Pending by Node"
5. ✅ Mostrar panel "HTTP Requests"
6. ✅ Mostrar panel "RabbitMQ Messages"
7. Mostrar los targets de Prometheus en http://localhost:9090/targets

**LO QUE EXPLICAS**: "Prometheus recolecta métricas de los microservicios, RabbitMQ, PostgreSQL y Outbox. Grafana visualiza latencia, errores, disponibilidad y sincronización distribuida en tiempo real."

