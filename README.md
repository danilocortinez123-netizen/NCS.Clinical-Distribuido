
# Sistema de Historia Clínica Distribuida (PostgreSQL + Docker)

Este repositorio contiene un laboratorio completo para simular una base de datos distribuida usando fragmentación manual sobre PostgreSQL, desplegado con Docker Compose.

## 🚀 Componentes

- `docker-compose.yml`: levanta 3 contenedores PostgreSQL (`pg_nodo1`, `pg_nodo2`, `pg_nodo3`)
- `nodo1.sql`, `nodo2.sql`, `nodo3.sql`: scripts SQL para cada nodo con el esquema replicado o fragmentado.
- `middleware.py`: script Python que consulta los 3 nodos como si fueran una única base.

## ⚙️ Requisitos

- Docker + Docker Compose
- Python 3.8+
- Dependencias Python:
```bash
pip install psycopg2-binary
```

## ▶️ Instrucciones de uso

1. Clonar el repositorio y entrar al directorio:
```bash
git clone <repo-url>
cd historia_clinica_distribuida
```

2. Levantar los nodos:
```bash
docker-compose up -d
```

3. Cargar los scripts en cada nodo:
```bash
psql -h localhost -p 5433 -U admin -d historia_clinica -f nodo1.sql
psql -h localhost -p 5434 -U admin -d historia_clinica -f nodo2.sql
psql -h localhost -p 5435 -U admin -d historia_clinica -f nodo3.sql
```

4. Ejecutar el middleware:
```bash
python middleware.py
```

## 🧪 Validación

Prueba insertar usuarios con diferentes `documento_id` y realiza consultas desde el middleware.

## 📂 Estructura del repositorio

```
.
├── docker-compose.yml
├── nodo1.sql
├── nodo2.sql
├── nodo3.sql
├── middleware.py
└── README.md
```

---

Autor: GPT Ingeniero Experto SRE  
