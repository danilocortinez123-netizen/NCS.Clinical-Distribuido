from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


class PatientIdentificationData(BaseModel):
    tipoDocumento: str = Field(..., description="Tipo de documento de identidad")
    numeroDocumento: str = Field(..., description="Número de documento de identidad")
    paisNacionalidad: str = Field(..., description="Código ISO del país de nacionalidad")
    nombreCompleto: str = Field(..., description="Nombre completo del paciente")
    fechaNacimiento: date = Field(..., description="Fecha de nacimiento")
    edad: int = Field(..., ge=0, le=150, description="Edad del paciente")
    unidadEdad: str = Field(default="1", description="1=Años, 2=Meses, 3=Días")
    sexo: str = Field(..., description="Sexo: male, female, other, unknown")
    genero: Optional[str] = Field(None, description="Identidad de género")
    ocupacion: Optional[str] = Field(None, description="Ocupación o profesión")
    voluntadAnticipada: Optional[str] = Field(None, description="true/false")
    categoriaDiscapacidad: Optional[str] = Field(None, description="Tipo de discapacidad")
    paisResidencia: str = Field(..., description="Código ISO del país de residencia")
    municipioResidencia: str = Field(..., description="Código DANE del municipio")
    etnia: Optional[str] = Field(None, description="Grupo étnico")

    class Config:
        json_schema_extra = {
            "example": {
                "tipoDocumento": "CC",
                "numeroDocumento": "1234567890",
                "paisNacionalidad": "CO",
                "nombreCompleto": "Juan Pérez García",
                "fechaNacimiento": "1985-03-15",
                "edad": 39,
                "unidadEdad": "1",
                "sexo": "male",
                "genero": "Masculino",
                "ocupacion": "Ingeniero",
                "voluntadAnticipada": "false",
                "categoriaDiscapacidad": "",
                "paisResidencia": "CO",
                "municipioResidencia": "11001",
                "etnia": "Ninguna",
            }
        }


class PatientResponse(BaseModel):
    success: bool
    message: str
    patient_id: Optional[str] = None
    fhir_resource: Optional[dict] = None
    sede: Optional[str] = None
    sync_status: Optional[str] = None
    event_type: Optional[str] = None
