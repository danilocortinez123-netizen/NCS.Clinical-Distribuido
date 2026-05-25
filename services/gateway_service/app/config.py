from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    service_name: str = "gateway-service"
    host: str = "0.0.0.0"
    port: int = 8000

    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"

    patient_service_url: str = "http://patient-service:8002"
    clinical_service_url: str = "http://clinical-service:8003"
    sync_service_url: str = "http://sync-service:8004"

    class Config:
        env_file = ".env"


settings = Settings()
