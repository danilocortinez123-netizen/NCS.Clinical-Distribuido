import os
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter()

FRONTEND_DIR = "/app/frontend/templates"

PAGES = {
    "/": "index.html",
    "/carga-hc": "carga-hc.html",
    "/consulta-hc": "consulta-hc.html",
    "/registro-paciente": "registro-paciente.html",
    "/hc": "firh.html",
    "/firh": "firh.html",
}

@router.get("/", response_class=HTMLResponse)
@router.get("/carga-hc", response_class=HTMLResponse)
@router.get("/carga-hc/", response_class=HTMLResponse)
@router.get("/consulta-hc", response_class=HTMLResponse)
@router.get("/consulta-hc/", response_class=HTMLResponse)
@router.get("/registro-paciente", response_class=HTMLResponse)
@router.get("/registro-paciente/", response_class=HTMLResponse)
@router.get("/hc", response_class=HTMLResponse)
@router.get("/hc/", response_class=HTMLResponse)
@router.get("/firh", response_class=HTMLResponse)
@router.get("/firh/", response_class=HTMLResponse)
async def serve_frontend(request: Request):
    path_key = request.url.path.rstrip("/")
    if path_key == "":
        path_key = "/"
    
    filename = PAGES.get(path_key, "index.html")
    path = f"/app/frontend/templates/{filename}"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página no encontrada")


@router.get("/paciente/{patient_id}", response_class=HTMLResponse)
async def patient_detail_page(patient_id: str):
    path = "/app/frontend/templates/detalle-paciente.html"
    try:
        with open(path, "r", encoding="utf-8") as f:
            html = f.read()
            html = html.replace("{{patient_id}}", patient_id)
            return html
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Página de detalle no encontrada")
