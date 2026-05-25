from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "patient-service"
    host: str = "0.0.0.0"
    port: int = 8002

    hapi_fhir_url: str = "http://hapi-fhir:8080/fhir"

    rabbitmq_host: str = "rabbitmq"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"

    events_exchange: str = "patient.exchange"

    events_db_host: str = "pg_nodo1"
    events_db_port: int = 5432
    events_db_user: str = "admin"
    events_db_password: str = "admin"
    events_db_name: str = "events_db"

    class Config:
        env_file = ".env"


settings = Settings()
