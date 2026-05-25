/**
 * ui-feedback.js — HIS Distribuido
 * Sistema global de retroalimentación visual.
 * Reemplaza alert(), confirm() y prompt() por toasts y modales enterprise.
 */

(function () {
  /* ---------- TOAST ---------- */
  const TOAST_DURATION = 4500;

  function _ensureToastContainer() {
    let el = document.getElementById('_ent_toast');
    if (!el) {
      el = document.createElement('div');
      el.id = '_ent_toast';
      el.style.cssText = `
        position:fixed; bottom:30px; right:30px; z-index:9999;
        display:flex; flex-direction:column; gap:0.6rem; align-items:flex-end;
        pointer-events:none;
      `;
      document.body.appendChild(el);
    }
    return el;
  }

  const ICONS = {
    success: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256"><path d="M173.66,98.34a8,8,0,0,1,0,11.32l-56,56a8,8,0,0,1-11.32,0l-24-24a8,8,0,0,1,11.32-11.32L112,148.69l50.34-50.35A8,8,0,0,1,173.66,98.34ZM232,128A104,104,0,1,1,128,24,104.11,104.11,0,0,1,232,128Zm-16,0a88,88,0,1,0-88,88A88.1,88.1,0,0,0,216,128Z"/></svg>`,
    error:   `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256"><path d="M236.8,188.09,149.35,36.22a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM120,104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm8,88a12,12,0,1,1,12-12A12,12,0,0,1,128,192Z"/></svg>`,
    warning: `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256"><path d="M236.8,188.09,149.35,36.22a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM120,104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm8,88a12,12,0,1,1,12-12A12,12,0,0,1,128,192Z"/></svg>`,
    info:    `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="currentColor" viewBox="0 0 256 256"><path d="M128,24A104,104,0,1,0,232,128,104.11,104.11,0,0,0,128,24Zm0,192a88,88,0,1,1,88-88A88.1,88.1,0,0,1,128,216Zm16-40a8,8,0,0,1-8,8,16,16,0,0,1-16-16V128a8,8,0,0,1,0-16,16,16,0,0,1,16,16v40A8,8,0,0,1,144,176ZM112,84a12,12,0,1,1,12,12A12,12,0,0,1,112,84Z"/></svg>`,
  };

  const COLORS = {
    success: { bg: '#166534', border: '#15803d' },
    error:   { bg: '#991b1b', border: '#b91c1c' },
    warning: { bg: '#854d0e', border: '#b45309' },
    info:    { bg: '#1e3a8a', border: '#1d4ed8' },
  };

  window.showToast = function (message, type = 'info') {
    const container = _ensureToastContainer();
    const c = COLORS[type] || COLORS.info;
    const icon = ICONS[type] || ICONS.info;

    const el = document.createElement('div');
    el.style.cssText = `
      background:${c.bg}; color:#fff; border:1px solid ${c.border};
      padding:0.85rem 1.2rem; border-radius:8px;
      box-shadow:0 8px 20px rgba(0,0,0,0.25);
      display:flex; align-items:center; gap:0.75rem;
      font-family:'Inter',sans-serif; font-size:0.9rem; font-weight:500;
      max-width:380px; pointer-events:auto;
      animation: _toastIn 0.3s ease;
    `;
    el.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(el);

    setTimeout(() => {
      el.style.opacity = '0';
      el.style.transition = 'opacity 0.4s';
      setTimeout(() => el.remove(), 400);
    }, TOAST_DURATION);
  };

  /* ---------- MODAL BASE ---------- */
  function _createOverlay() {
    const o = document.createElement('div');
    o.id = '_ent_overlay';
    o.style.cssText = `
      position:fixed; inset:0; background:rgba(15,23,42,0.6);
      backdrop-filter:blur(3px); z-index:10000;
      display:flex; align-items:center; justify-content:center;
      animation: _fadeIn 0.2s ease;
    `;
    return o;
  }

  function _createModalBox(content) {
    const box = document.createElement('div');
    box.style.cssText = `
      background:#fff; border-radius:12px;
      padding:2rem; width:90%; max-width:480px;
      box-shadow:0 20px 40px rgba(0,0,0,0.2);
      font-family:'Inter',sans-serif;
      animation: _slideUp 0.25s ease;
    `;
    box.innerHTML = content;
    return box;
  }

  const TYPE_COLORS = {
    success: '#166534', error: '#991b1b', warning: '#b45309',
    info: '#1e3a8a', danger: '#991b1b',
  };

  const TYPE_BG = {
    success: '#f0fdf4', error: '#fef2f2', warning: '#fffbeb',
    info: '#eff6ff', danger: '#fef2f2',
  };

  function _inject_keyframes() {
    if (document.getElementById('_ent_kf')) return;
    const s = document.createElement('style');
    s.id = '_ent_kf';
    s.textContent = `
      @keyframes _toastIn { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:none; } }
      @keyframes _fadeIn  { from { opacity:0; } to { opacity:1; } }
      @keyframes _slideUp { from { opacity:0; transform:translateY(24px); } to { opacity:1; transform:none; } }
      ._ent_btn {
        display:inline-flex; align-items:center; gap:0.4rem;
        padding:0.6rem 1.3rem; border-radius:6px; border:none;
        font-weight:600; font-size:0.9rem; cursor:pointer;
        font-family:'Inter',sans-serif; transition:filter 0.15s;
      }
      ._ent_btn:hover { filter:brightness(0.9); }
      ._ent_btn_primary { background:#1e3a8a; color:#fff; }
      ._ent_btn_danger  { background:#991b1b; color:#fff; }
      ._ent_btn_cancel  { background:#f1f5f9; color:#334155; border:1px solid #e2e8f0; }
    `;
    document.head.appendChild(s);
  }

  /* ---------- CONFIRM MODAL ---------- */
  window.showConfirmModal = function ({
    title = '¿Confirmar acción?',
    message = '',
    type = 'info',
    confirmText = 'Confirmar',
    cancelText = 'Cancelar',
    onConfirm = () => {},
    onCancel = () => {},
  }) {
    _inject_keyframes();
    const overlay = _createOverlay();
    const tc = TYPE_COLORS[type] || TYPE_COLORS.info;
    const tbg = TYPE_BG[type] || TYPE_BG.info;
    const icon = ICONS[type] || ICONS.info;
    const isDanger = type === 'error' || type === 'danger';

    const box = _createModalBox(`
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
        <div style="width:40px;height:40px;border-radius:8px;background:${tbg};display:flex;align-items:center;justify-content:center;color:${tc};flex-shrink:0;">${icon}</div>
        <h3 style="margin:0;color:#0f172a;font-size:1.1rem;font-weight:700;">${title}</h3>
      </div>
      <p style="color:#475569;font-size:0.9rem;margin:0 0 1.5rem 0;line-height:1.6;">${message}</p>
      <div style="display:flex;justify-content:flex-end;gap:0.75rem;">
        <button id="_ent_cancel" class="_ent_btn _ent_btn_cancel">${cancelText}</button>
        <button id="_ent_confirm" class="_ent_btn ${isDanger ? '_ent_btn_danger' : '_ent_btn_primary'}">${confirmText}</button>
      </div>
    `);

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    overlay.querySelector('#_ent_confirm').onclick = () => {
      overlay.remove();
      onConfirm();
    };
    overlay.querySelector('#_ent_cancel').onclick = () => {
      overlay.remove();
      onCancel();
    };
    overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); onCancel(); } };
  };

  /* ---------- INFO MODAL ---------- */
  window.showInfoModal = function ({
    title = 'Información',
    message = '',
    type = 'info',
    buttonText = 'Cerrar',
    onClose = () => {},
  }) {
    _inject_keyframes();
    const overlay = _createOverlay();
    const tc = TYPE_COLORS[type] || TYPE_COLORS.info;
    const tbg = TYPE_BG[type] || TYPE_BG.info;
    const icon = ICONS[type] || ICONS.info;

    const box = _createModalBox(`
      <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
        <div style="width:40px;height:40px;border-radius:8px;background:${tbg};display:flex;align-items:center;justify-content:center;color:${tc};flex-shrink:0;">${icon}</div>
        <h3 style="margin:0;color:#0f172a;font-size:1.1rem;font-weight:700;">${title}</h3>
      </div>
      <div style="color:#475569;font-size:0.9rem;margin:0 0 1.5rem 0;line-height:1.6;">${message}</div>
      <div style="display:flex;justify-content:flex-end;">
        <button id="_ent_ok" class="_ent_btn _ent_btn_primary">${buttonText}</button>
      </div>
    `);

    overlay.appendChild(box);
    document.body.appendChild(overlay);

    overlay.querySelector('#_ent_ok').onclick = () => { overlay.remove(); onClose(); };
    overlay.onclick = (e) => { if (e.target === overlay) { overlay.remove(); onClose(); } };
  };

  window.closeModal = function () {
    const o = document.getElementById('_ent_overlay');
    if (o) o.remove();
  };
})();
