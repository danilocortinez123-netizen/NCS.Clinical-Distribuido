#!/bin/bash

cd ~/historia-clinica-distribuida

echo "--- Activating virtual environment ---"
source .venv/bin/activate

echo "--- Upgrading pip ---"
python -m pip install --upgrade pip setuptools wheel

echo "--- Finding used imports ---"
python - <<'PY'
import ast, os
mods=set()
for root, dirs, files in os.walk("."):
    if ".env" in root or ".venv" in root or "__pycache__" in root:
        continue
    for f in files:
        if f.endswith(".py"):
            path=os.path.join(root,f)
            try:
                tree=ast.parse(open(path, encoding="utf-8").read())
                for n in ast.walk(tree):
                    if isinstance(n, ast.Import):
                        for a in n.names:
                            mods.add(a.name.split(".")[0])
                    elif isinstance(n, ast.ImportFrom) and n.module:
                        mods.add(n.module.split(".")[0])
            except Exception as e:
                pass
print("Usados en el código:")
print(", ".join(sorted(mods)))
PY

echo "--- Testing main imports ---"
python - <<'PY'
mods = [
"fastapi","uvicorn","httpx","psycopg2","pika","pydantic","dotenv",
"fhir","prometheus_client","prometheus_fastapi_instrumentator",
"requests","aio_pika","asyncpg","sqlalchemy","multipart","jinja2"
]
missing=[]
for m in mods:
    try:
        __import__(m)
        print("OK", m)
    except Exception as e:
        print("MISSING", m, e)
        missing.append(m)
print("FALTAN_A_INSTALAR:", missing)
PY

echo "--- Installing common missing packages ---"
pip install \
  fastapi \
  uvicorn[standard] \
  httpx \
  psycopg2-binary \
  pika \
  pydantic \
  python-dotenv \
  fhir.resources \
  prometheus-fastapi-instrumentator \
  prometheus-client \
  requests \
  aio-pika \
  asyncpg \
  sqlalchemy \
  python-multipart \
  jinja2

echo "--- Reinstalling all requirements.txt ---"
# using || true because some older hardcoded packages in requirements.txt (like pydantic-core)
# lack python 3.13 wheels and fail to build without rust.
find . -name "requirements.txt" -print0 | xargs -0 -I {} pip install -r "{}" || true

echo "--- Verifying again ---"
python - <<'PY'
mods = [
"fastapi","uvicorn","httpx","psycopg2","pika","pydantic","dotenv",
"fhir","prometheus_client","prometheus_fastapi_instrumentator",
"requests","aio_pika","asyncpg","sqlalchemy","multipart","jinja2"
]
missing=[]
for m in mods:
    try:
        __import__(m)
        print("OK", m)
    except Exception as e:
        print("MISSING", m, e)
        missing.append(m)
if missing:
    raise SystemExit("Todavía faltan: " + str(missing))
print("TODAS LAS DEPENDENCIAS PRINCIPALES ESTÁN OK")
PY

echo "--- Saving requirements ---"
pip freeze > requirements-local.txt
echo "DONE"
