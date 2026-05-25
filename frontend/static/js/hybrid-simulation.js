const STORAGE_KEY = 'hcd_simulation_state';

const defaultState = {
    sedes: { Sincelejo: 'ACTIVO', Bogotá: 'ACTIVO', Medellín: 'ACTIVO' },
    cloud: 'ACTIVO', pacientes: [], eventos: []
};

// Fallback logic
function getFallbackState() {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : defaultState;
}

function saveFallbackState(state) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    window.dispatchEvent(new Event('hcd_state_changed'));
}

window.HybridSim = {
    _useFallback: false,

    async initHybridState() {
        if (!localStorage.getItem(STORAGE_KEY)) {
            saveFallbackState(defaultState);
        }
    },

    async getNodes() {
        try {
            const res = await fetch('/api/nodes/status');
            if (!res.ok) throw new Error();
            return await res.json();
        } catch {
            console.warn("Modo demo local: backend no disponible (getNodes)");
            this._useFallback = true;
            return getFallbackState().sedes;
        }
    },

    async setNodeStatus(nodeId, status) {
        try {
            const endpoint = status === 'OFFLINE' ? `/api/nodes/${nodeId}/fail` : `/api/nodes/${nodeId}/restore`;
            const res = await fetch(endpoint, { method: 'POST' });
            if (!res.ok) throw new Error();
        } catch {
            console.warn("Modo demo local: backend no disponible (setNodeStatus)");
            const state = getFallbackState();
            state.sedes[nodeId] = status;
            saveFallbackState(state);
        }
        window.dispatchEvent(new Event('hcd_state_changed'));
    },

    async getCloudStatus() {
        try {
            const res = await fetch('/api/dashboard/status');
            if (!res.ok) throw new Error();
            return (await res.json()).cloud;
        } catch {
            return getFallbackState().cloud;
        }
    },

    async setCloudStatus(status) {
        try {
            const endpoint = status === 'OFFLINE' ? `/api/cloud/fail` : `/api/cloud/restore`;
            const res = await fetch(endpoint, { method: 'POST' });
            if (!res.ok) throw new Error();
        } catch {
            const state = getFallbackState();
            state.cloud = status;
            saveFallbackState(state);
        }
        window.dispatchEvent(new Event('hcd_state_changed'));
    },

    async createPatient(data) {
        try {
            const res = await fetch('/api/v1/patient/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!res.ok) throw new Error(await res.text());
            return await res.json(); // contains patient_id, sede, sync_status, event_id
        } catch (err) {
            console.warn("Modo demo local: backend no disponible (createPatient)");
            const state = getFallbackState();
            if (state.sedes[data.sede] === 'OFFLINE') throw new Error(`La sede ${data.sede} está OFFLINE.`);
            
            const isCloudActive = state.cloud === 'ACTIVO';
            const newPatient = {
                id: 'P-' + Date.now(),
                fecha_registro: new Date().toISOString(),
                estado_sync: isCloudActive ? 'SINCRONIZADO' : 'PENDIENTE_SYNC',
                timeline: [],
                ...data
            };
            state.pacientes.push(newPatient);
            
            const newEvent = {
                id: 'EV-' + Date.now(),
                estado: isCloudActive ? 'PROCESADO' : 'PENDIENTE',
                fecha_creacion: new Date().toISOString(),
                tipo: 'PatientCreated', paciente_id: newPatient.id, sede: newPatient.sede
            };
            state.eventos.push(newEvent);
            
            saveFallbackState(state);
            return newPatient;
        }
    },

    async getPatients() {
        try {
            const res = await fetch('/api/v1/patient/');
            if (!res.ok) throw new Error();
            return await res.json();
        } catch {
            return getFallbackState().pacientes;
        }
    },

    async getPatientById(id) {
        try {
            const res = await fetch(`/api/v1/patient/${id}`);
            if (!res.ok) throw new Error();
            return await res.json();
        } catch {
            return getFallbackState().pacientes.find(p => p.id === id || p.documento === id);
        }
    },

    async createClinicalRecord(patient_id, sede, record) {
        try {
            const payload = {
                patient_id, sede,
                encounter: { encounter: record.encounter },
                observations: { observation: record.observation },
                condition: { condition: record.condition },
                medication_request: { medication: record.medication }
            };
            const res = await fetch('/api/v1/clinical/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) throw new Error();
        } catch {
            console.warn("Modo demo local");
            const state = getFallbackState();
            const p = state.pacientes.find(x => x.id === patient_id);
            if (p) {
                p.timeline = p.timeline || [];
                p.timeline.push(record);
            }
            saveFallbackState(state);
        }
    },

    async processPendingEvents() {
        try {
            const res = await fetch('/api/sync/process-pending', { method: 'POST' });
            if (!res.ok) throw new Error(await res.text());
        } catch {
            const state = getFallbackState();
            if (state.cloud === 'OFFLINE') return;
            state.eventos.forEach(ev => {
                if (ev.estado === 'PENDIENTE') {
                    ev.estado = 'PROCESADO';
                    const p = state.pacientes.find(x => x.id === ev.paciente_id);
                    if (p) p.estado_sync = 'SINCRONIZADO';
                }
            });
            saveFallbackState(state);
        }
        window.dispatchEvent(new Event('hcd_state_changed'));
    },

    async syncPatient(patientId) {
        await this.processPendingEvents();
    },

    async getDashboardStats() {
        try {
            const res = await fetch('/api/dashboard/status');
            if (!res.ok) throw new Error();
            return await res.json();
        } catch {
            const state = getFallbackState();
            const anyOffline = Object.values(state.sedes).includes('OFFLINE');
            const pending = state.eventos.filter(e => e.estado === 'PENDIENTE').length;
            const processed = state.eventos.filter(e => e.estado === 'PROCESADO').length;
            
            const pCount = {};
            state.pacientes.forEach(p => { pCount[p.sede] = (pCount[p.sede] || 0) + 1 });

            return {
                nodes: state.sedes, cloud: state.cloud, patients: pCount,
                pending_events: pending, processed_events: processed,
                mode: state.cloud === 'OFFLINE' ? 'CLOUD_OFFLINE' : (anyOffline ? 'NODE_FAILURE' : 'HIBRIDO_NORMAL')
            };
        }
    }
};

window.HybridSim.initHybridState();
