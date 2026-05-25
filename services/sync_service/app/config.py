from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "sync-service"
    host: str = "0.0.0.0"
    port: int = 8004

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    rabbitmq_exchange: str = "historia_clinica.events"

    events_db_host: str = "pg_nodo1"
    events_db_port: int = 5432
    events_db_user: str = "admin"
    events_db_password: str = "admin"
    events_db_name: str = "historia_clinica"
    
    hapi_fhir_url: str = "http://hapi-fhir:8080/fhir"
    auto_sync_enabled: bool = False

    class Config:
        env_file = ".env"


settings = Settings()
