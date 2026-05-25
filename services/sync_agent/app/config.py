from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "sync-agent"
    host: str = "0.0.0.0"
    port: int = 8005

    local_rabbitmq_host: str = "local_rabbitmq"
    local_rabbitmq_port: int = 5672
    local_rabbitmq_user: str = "guest"
    local_rabbitmq_password: str = "guest"

    cloud_rabbitmq_host: str = "cloud_rabbitmq"
    cloud_rabbitmq_port: int = 5672
    cloud_rabbitmq_user: str = "guest"
    cloud_rabbitmq_password: str = "guest"

    events_db_host: str = "local_pg"
    events_db_port: int = 5432
    events_db_user: str = "admin"
    events_db_password: str = "admin"
    events_db_name: str = "events_db"

    poll_interval: int = 5
    circuit_breaker_threshold: int = 3
    circuit_breaker_reset_seconds: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
