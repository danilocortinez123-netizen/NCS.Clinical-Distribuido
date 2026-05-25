#!/bin/bash
set -e

cd ~/historia-clinica-distribuida

echo "--- PASO 2: Actualizando .gitignore ---"
cat << 'EOF' > .gitignore
.env/
.venv/
__pycache__/
*.pyc
*.pyo
*.log
*.bak
*.sql
backup_*.sql
backups/
.env.*
!.env.example

node_modules/
dist/
build/

.vscode/
.idea/

*.db
*.sqlite

prometheus_data/
grafana_data/

.DS_Store
EOF

echo "--- PASO 3: Creando .env.example ---"
cat << 'EOF' > .env.example
DATABASE_URL=postgresql://admin:admin@pg_nodo1:5432/historia_clinica
RABBITMQ_HOST=rabbitmq
FHIR_BASE_URL=http://hapi-fhir:8080/fhir
EOF

echo "--- PASO 4: Inicializando Git ---"
if [ ! -d ".git" ]; then
    git init
    git branch -m main || true
fi

echo "--- PASO 5: Estado Inicial ---"
git status --short

echo "--- PASO 6: Verificando secretos ---"
find . -type f \( -name "*.sql" -o -name "*.bak" -o -name "*.log" -o -name ".env" -o -path "*/.env/*" -o -path "*/.venv/*" \) > /tmp/secretos_encontrados.txt
echo "Archivos sensibles encontrados (no se agregarán):"
cat /tmp/secretos_encontrados.txt | head -n 10
echo "..."

echo "--- PASO 7: Fase 1 ---"
git add docker-compose.yml README.md .gitignore .env.example Makefile package.json init-databases.sh 2>/dev/null || true
git commit -m "fase 1: estructura base docker y configuracion inicial" || true

echo "--- PASO 8: Fase 2 ---"
git add services/ 2>/dev/null || true
git commit -m "fase 2: microservicios FastAPI para gateway pacientes clinica y sincronizacion" || true

echo "--- PASO 9: Fase 3 ---"
git add frontend/ 2>/dev/null || true
git commit -m "fase 3: interfaces clinicas de registro consulta carga detalle y dashboard" || true

echo "--- PASO 10: Fase 4 ---"
# Check if there are changes in services related to outbox/sync that weren't committed
# Since git add services/ was done in phase 2, there might be nothing left.
git add shared/ 2>/dev/null || true
git commit -m "fase 4: integracion outbox rabbitmq y sincronizacion FHIR" || true

echo "--- PASO 11: Fase 5 ---"
git add scripts/ dedup_patients.py test_upsert.py test-mvp-fhir.sh 2>/dev/null || true
git commit -m "fase 5: importacion distribuida upsert y prevencion de duplicados" || true

echo "--- PASO 12: Fase 6 ---"
git add monitoring/ prometheus.yml prom.yml grafana/ 2>/dev/null || true
git commit -m "fase 6: observabilidad con prometheus grafana y exporters" || true

echo "--- PASO 13: Fase 7 ---"
git add *.md requirements-local.txt docs/ 2>/dev/null || true
git commit -m "fase 7: documentacion de rubrica demo entorno y mantenimiento" || true

# Add any remaining python scripts or configurations that shouldn't be ignored
git add *.py *.sh 2>/dev/null || true
git commit -m "fase 8: scripts auxiliares de operacion" || true

echo "--- PASO 14: Log de Git ---"
git log --oneline --decorate --graph --all -n 15

echo "--- PASO 15: Estado Final ---"
git status
