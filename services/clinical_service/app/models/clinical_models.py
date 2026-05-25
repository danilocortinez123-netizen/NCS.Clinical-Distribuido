from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


class EncounterCreate(BaseModel):
    documento_id: int = Field(..., description="Documento del paciente")
    entidad_salud: Optional[str] = None
    fecha_ingreso: Optional[datetime] = None
    modalidad_entrega: Optional[str] = None
    entorno_atencion: Optional[str] = None
    via_ingreso: Optional[str] = None
    causa_atencion: Optional[str] = None
    fecha_triage: Optional[datetime] = None
    clasificacion_triage: Optional[str] = None


class EncounterResponse(BaseModel):
    atencion_id: int
    documento_id: int
    entidad_salud: Optional[str] = None
    fecha_ingreso: Optional[str] = None
    modalidad_entrega: Optional[str] = None
    entorno_atencion: Optional[str] = None
    via_ingreso: Optional[str] = None
    causa_atencion: Optional[str] = None
    fecha_triage: Optional[str] = None
    clasificacion_triage: Optional[str] = None
    nodo: str


class ObservationCreate(BaseModel):
    documento_id: int
    atencion_id: int
    tecnologia_id: str = Field(default="", description="UUID")
    descripcion_medicamento: Optional[str] = None
    dosis: Optional[str] = None
    via_administracion: Optional[str] = None
    frecuencia: Optional[str] = None
    dias_tratamiento: Optional[int] = None
    unidades_aplicadas: Optional[int] = None
    id_personal_salud: Optional[str] = None
    finalidad_tecnologia: Optional[str] = None


class ConditionCreate(BaseModel):
    documento_id: int
    atencion_id: int
    tipo_diagnostico_ingreso: Optional[str] = None
    diagnostico_ingreso: Optional[str] = None
    tipo_diagnostico_egreso: Optional[str] = None
    diagnostico_egreso: Optional[str] = None
    diagnostico_rel1: Optional[str] = None
    diagnostico_rel2: Optional[str] = None
    diagnostico_rel3: Optional[str] = None


class DischargeCreate(BaseModel):
    documento_id: int
    atencion_id: int
    fecha_salida: Optional[datetime] = None
    condicion_salida: Optional[str] = None
    diagnostico_muerte: Optional[str] = None
    codigo_prestador: Optional[str] = None
    tipo_incapacidad: Optional[str] = None
    dias_incapacidad: Optional[int] = None
    dias_lic_maternidad: Optional[int] = None
    alergias: Optional[str] = None
    antecedente_familiar: Optional[str] = None
    riesgos_ocupacionales: Optional[str] = None
    responsable_egreso: Optional[str] = None


class QueryRequest(BaseModel):
    query: str


class QueryResult(BaseModel):
    resultados: list[dict[str, Any]]
    nodos_estado: list[dict[str, Any]]
