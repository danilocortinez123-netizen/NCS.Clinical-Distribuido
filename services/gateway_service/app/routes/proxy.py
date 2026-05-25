from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
from typing import Optional

from ..config import settings

router = APIRouter()
client: Optional[httpx.AsyncClient] = None


def get_client() -> httpx.AsyncClient:
    global client
    if client is None:
        client = httpx.AsyncClient(timeout=30.0)
    return client


SERVICE_ROUTES = {
    "patient": {
        "prefix": "/api/v1/patient",
        "target": settings.patient_service_url,
    },
    "clinical": {
        "prefix": "/api/v1/clinical",
        "target": settings.clinical_service_url,
    },
    "admin": {
        "prefix": "/api/v1/admin",
        "target": settings.sync_service_url,
    },
}


@router.api_route("/api/v1/patient/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_patient(path: str, request: Request):
    return await proxy_request("patient", f"/{path}", request)


@router.api_route("/api/v1/clinical/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_clinical(path: str, request: Request):
    return await proxy_request("clinical", f"/{path}", request)

@router.api_route("/api/v1/admin/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_admin(path: str, request: Request):
    return await proxy_request("admin", f"/{path}", request)


async def proxy_request(service: str, path: str, request: Request):
    cfg = SERVICE_ROUTES.get(service)
    if not cfg:
        raise HTTPException(status_code=404, detail="Servicio no encontrado")

    target_url = f"{cfg['target']}{cfg['prefix']}{path}"
    body = await request.body()
    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        client = get_client()
        response = await client.request(
            method=request.method,
            url=target_url,
            content=body,
            headers=headers,
            params=request.query_params,
        )
        return JSONResponse(
            content=response.json() if response.content else None,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
    except httpx.RequestError as e:
        return JSONResponse(
            status_code=502,
            content={"error": f"Servicio {service} no disponible", "detail": str(e)},
        )


@router.on_event("shutdown")
async def shutdown():
    global client
    if client:
        await client.aclose()
