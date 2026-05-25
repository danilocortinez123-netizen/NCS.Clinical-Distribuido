/**
 * hybrid-status.js — HIS Distribuido
 * Gestión del estado lógico/visual de nodos y Cloud.
 * NO almacena pacientes. Solo controla la topología operativa.
 */

(function () {
  const STORAGE_KEY = 'his_hybrid_status';
  const SEDE_KEY    = 'activeSede';

  const DEFAULT_STATUS = {
    Sincelejo: 'ACTIVE',
    Bogota:    'ACTIVE',
    Medellin:  'ACTIVE',
    Cloud:     'ACTIVE',
  };

  // Alias de normalización: UI usa tildes, store usa sin tildes
  const ALIAS = {
    'Bogotá':   'Bogota',
    'Medellín': 'Medellin',
    'Sincelejo':'Sincelejo',
    'Bogota':   'Bogota',
    'Medellin': 'Medellin',
    'Cloud':    'Cloud',
  };

  function _normalize(node) {
    return ALIAS[node] || node;
  }

  function _load() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || { ...DEFAULT_STATUS };
    } catch {
      return { ...DEFAULT_STATUS };
    }
  }

  function _save(state) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    // Dispatch event so all pages can react
    window.dispatchEvent(new CustomEvent('hybridStatusChange', { detail: state }));
  }

  window.getHybridStatus = function () { return _load(); };

  window.setNodeOffline = function (node) {
    const s = _load();
    s[_normalize(node)] = 'OFFLINE';
    _save(s);
  };

  window.setNodeOnline = function (node) {
    const s = _load();
    s[_normalize(node)] = 'ACTIVE';
    _save(s);
  };

  window.restoreAllNodes = function () {
    _save({ ...DEFAULT_STATUS });
  };

  window.isNodeActive = function (node) {
    return _load()[_normalize(node)] === 'ACTIVE';
  };

  window.isCloudActive = function () {
    return _load()['Cloud'] === 'ACTIVE';
  };

  window.getActiveSede = function () {
    return sessionStorage.getItem(SEDE_KEY) || 'Sincelejo';
  };

  window.setActiveSede = function (sede) {
    sessionStorage.setItem(SEDE_KEY, sede);
    window.dispatchEvent(new CustomEvent('activeSedeChange', { detail: sede }));
  };

  /* ---------- UI: Sede Selector (shared) ---------- */
  window.initSedeSelector = function (selectorId, onChange) {
    const sel = document.getElementById(selectorId);
    if (!sel) return;
    const activeSede = getActiveSede();
    sel.querySelectorAll('.sede-pill').forEach(p => {
      p.classList.toggle('active', p.dataset.sede === activeSede);
    });
    sel.querySelectorAll('.sede-pill').forEach(pill => {
      pill.addEventListener('click', e => {
        const sede = e.target.closest('.sede-pill').dataset.sede;
        setActiveSede(sede);
        sel.querySelectorAll('.sede-pill').forEach(p =>
          p.classList.toggle('active', p.dataset.sede === sede)
        );
        if (typeof onChange === 'function') onChange(sede);
      });
    });
  };

  /* ---------- UI: Status Ring badge ---------- */
  window.getNodeBadgeHtml = function (node) {
    const key = _normalize(node);
    const status = _load()[key];
    if (status === 'ACTIVE') {
      return `<span style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.75rem;color:#166534;background:#dcfce7;padding:0.15rem 0.5rem;border-radius:10px;font-weight:600;">● Activo</span>`;
    } else if (status === 'OFFLINE') {
      return `<span style="display:inline-flex;align-items:center;gap:0.3rem;font-size:0.75rem;color:#991b1b;background:#fee2e2;padding:0.15rem 0.5rem;border-radius:10px;font-weight:600;">● Offline</span>`;
    }
    return `<span style="font-size:0.75rem;color:#854d0e;background:#fef9c3;padding:0.15rem 0.5rem;border-radius:10px;font-weight:600;">Desconocido</span>`;
  };

})();
