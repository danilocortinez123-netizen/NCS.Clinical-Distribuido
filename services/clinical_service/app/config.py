from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "clinical-service"
    host: str = "0.0.0.0"
    port: int = 8003

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    events_exchange: str = "clinical.exchange"

    events_db_host: str = "pg_nodo1"
    events_db_port: int = 5432
    events_db_user: str = "admin"
    events_db_password: str = "admin"
    events_db_name: str = "events_db"

    local_db_host: str = ""
    local_db_port: int = 5432
    local_db_user: str = ""
    local_db_password: str = ""
    local_db_name: str = ""

    class Config:
        env_file = ".env"


settings = Settings()

NODES_CONFIG = [
    {"host": "pg_nodo1", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "shard": "documento_id < 4000000000", "display": "Nodo 1"},
    {"host": "pg_nodo2", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "shard": "documento_id >= 4000000000 AND < 7000000000", "display": "Nodo 2"},
    {"host": "pg_nodo3", "port": 5432, "user": "admin", "password": "admin", "dbname": "historia_clinica", "shard": "documento_id >= 7000000000", "display": "Nodo 3"},
]


def get_node_for_document(documento_id: int) -> dict:
    if settings.local_db_host:
        return {
            "host": settings.local_db_host,
            "port": settings.local_db_port,
            "user": settings.local_db_user or "admin",
            "password": settings.local_db_password or "admin",
            "dbname": settings.local_db_name or "historia_clinica",
            "display": "Local Node",
        }
    if documento_id < 4000000000:
        return NODES_CONFIG[0]
    elif documento_id < 7000000000:
        return NODES_CONFIG[1]
    return NODES_CONFIG[2]
