import re

with open('/home/jesus/historia-clinica-distribuida/frontend/templates/detalle-paciente.html', 'r') as f:
    content = f.read()

# Update CSS for enterprise
css_pattern = r'<style>.*?</style>'
new_css = """<style>
        :root { 
            --ent-bg: #f8fafc; 
            --ent-blue: #1e3a8a; 
            --ent-light-blue: #eff6ff; 
            --ent-dark: #0f172a; 
            --ent-card: #ffffff; 
            --ent-border: #e2e8f0;
            --ent-text: #334155;
            --ent-muted: #64748b;
        }
        body { font-family: 'Inter', sans-serif; background: var(--ent-bg); margin: 0; display: flex; min-height: 100vh; color: var(--ent-text); }
        .sidebar { width: 250px; background: var(--ent-dark); color: white; padding: 1.5rem; display: flex; flex-direction: column; }
        .sidebar h2 { font-size: 1.2rem; margin-bottom: 2rem; display: flex; align-items: center; gap: 0.5rem; color: #f8fafc; font-weight: 600; }
        .nav-item { padding: 0.8rem 1rem; border-radius: 6px; color: #94a3b8; text-decoration: none; display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; transition: all 0.2s; font-size: 0.95rem; }
        .nav-item:hover, .nav-item.active { background: #1e293b; color: white; border-left: 3px solid var(--ent-blue); }
        .main { flex: 1; padding: 2rem; overflow-y: auto; }
        
        .header-card { background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; border-radius: 8px; padding: 2rem; margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }
        .header-card h1 { margin: 0 0 0.5rem 0; display: flex; align-items: center; gap: 0.5rem; }
        .badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; display: inline-flex; align-items: center; gap: 0.3rem; background: rgba(255,255,255,0.2); backdrop-filter: blur(5px); }
        
        .grid-2 { display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }
        
        .card { background: var(--ent-card); border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid var(--ent-border); padding: 1.5rem; margin-bottom: 1.5rem; }
        .card-title { font-size: 1.1rem; font-weight: 700; color: #0f172a; margin: 0 0 1.2rem 0; display: flex; align-items: center; gap: 0.5rem; border-bottom: 1px solid var(--ent-border); padding-bottom: 0.8rem; }
        
        .timeline { position: relative; padding-left: 2rem; margin: 1rem 0; }
        .timeline::before { content: ''; position: absolute; left: 6px; top: 0; bottom: 0; width: 2px; background: #e2e8f0; }
        .tl-item { position: relative; margin-bottom: 1.5rem; }
        .tl-item::before { content: ''; position: absolute; left: -2rem; top: 0.2rem; width: 14px; height: 14px; border-radius: 50%; background: var(--ent-blue); border: 3px solid white; box-shadow: 0 0 0 2px var(--ent-blue); }
        .tl-item.sync::before { background: #15803d; box-shadow: 0 0 0 2px #15803d; }
        .tl-time { font-size: 0.8rem; color: #64748b; font-weight: 600; }
        .tl-title { font-weight: 700; color: #0f172a; margin: 0.2rem 0; }
        .tl-desc { font-size: 0.9rem; color: #475569; }
        
        .btn { padding: 0.6rem 1.2rem; border-radius: 4px; font-weight: 600; cursor: pointer; border: 1px solid transparent; display:inline-flex; align-items:center; gap:0.5rem; text-decoration: none; font-size: 0.9rem; transition: all 0.2s;}
        .btn-outline { background: white; border-color: #cbd5e1; color: var(--ent-text); }
        .btn-outline:hover { background: #f1f5f9; }
        
        .fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
        .field { font-size: 0.9rem; }
        .field span { display: block; font-weight: 600; color: #64748b; font-size: 0.8rem; margin-bottom: 0.2rem; }
        .field strong { color: #0f172a; }
        
        .sede-selector { display:flex; gap: 0.5rem; }
        .sede-pill { padding: 0.4rem 1rem; border: 1px solid #cbd5e1; border-radius: 16px; cursor: pointer; font-size: 0.85rem; font-weight: 600; color: var(--ent-muted); background: white; transition: all 0.2s; }
        .sede-pill.active { background: var(--ent-light-blue); border-color: #93c5fd; color: var(--ent-blue); }
        
        .fhir-card { border: 1px solid var(--ent-border); border-radius: 6px; padding: 1rem; margin-bottom: 1rem; background: #fafaf9;}
        .fhir-card-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; font-weight: 600; }
        .badge-status { padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; background: #dcfce7; color: #166534; font-weight: 600;}
    </style>"""
content = re.sub(css_pattern, new_css, content, flags=re.DOTALL)

# Update FHIR Mapeo
fhir_pattern = r'<div class="card">\s*<h3 class="card-title"><i class="ph ph-code"></i> Recursos FHIR R4</h3>.*?</div>'
new_fhir = """<div class="card">
                    <h3 class="card-title"><i class="ph ph-code"></i> Mapeo FHIR R4</h3>
                    
                    <div class="fhir-card">
                        <div class="fhir-card-title">
                            <span><i class="ph ph-user"></i> Patient</span>
                            <span class="badge-status">Generado</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">Campos incluidos: 1 al 15 (Identificación)</div>
                        <button class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="showFhir('Patient')">Ver JSON</button>
                    </div>

                    <div class="fhir-card">
                        <div class="fhir-card-title">
                            <span><i class="ph ph-hospital"></i> Encounter</span>
                            <span class="badge-status">Generado</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">Campos incluidos: 16-24, 40-57 (Atención y Egreso)</div>
                        <button class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="showFhir('Encounter')">Ver JSON</button>
                    </div>

                    <div class="fhir-card">
                        <div class="fhir-card-title">
                            <span><i class="ph ph-pill"></i> MedicationRequest</span>
                            <span class="badge-status">Pendiente</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">Campos incluidos: 25-32 (Tecnologías)</div>
                        <button class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="showFhir('MedicationRequest')">Ver JSON</button>
                    </div>

                    <div class="fhir-card">
                        <div class="fhir-card-title">
                            <span><i class="ph ph-stethoscope"></i> Condition</span>
                            <span class="badge-status">Generado</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-bottom: 0.5rem;">Campos incluidos: 33-39 (Diagnósticos)</div>
                        <button class="btn btn-outline" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="showFhir('Condition')">Ver JSON</button>
                    </div>
                    
                    <div id="fhir-viewer" style="display: none; margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 1rem;">
                        <h4 id="fhir-viewer-title" style="margin-top:0">JSON</h4>
                        <pre><code id="fhir-pre" style="background: #0f172a; color: #e2e8f0; padding: 1rem; border-radius: 6px; display: block; overflow-x: auto; font-size: 0.85rem;"></code></pre>
                    </div>
                </div>"""
content = re.sub(fhir_pattern, new_fhir, content, flags=re.DOTALL)

with open('/home/jesus/historia-clinica-distribuida/frontend/templates/detalle-paciente.html', 'w') as f:
    f.write(content)
