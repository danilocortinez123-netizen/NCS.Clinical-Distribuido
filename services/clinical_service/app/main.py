from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routes.clinical_routes import router as clinical_router

app = FastAPI(
    title="Clinical Service - Historia Clínica Distribuida",
    description="Microservicio de datos clínicos con sharding PostgreSQL",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from prometheus_fastapi_instrumentator import Instrumentator

app.include_router(clinical_router)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.service_name}
