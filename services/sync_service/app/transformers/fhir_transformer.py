from fhir.resources.patient import Patient
from fhir.resources.identifier import Identifier
from fhir.resources.humanname import HumanName
from fhir.resources.address import Address
from fhir.resources.extension import Extension
from fhir.resources.codeableconcept import CodeableConcept
from fhir.resources.coding import Coding
from typing import Any


class FHIRTransformer:

    @staticmethod
    def to_fhir_patient(data: dict[str, Any]) -> Patient:
        numero_doc = data.get("numeroDocumento") or data.get("documento") or "UNKNOWN"
        tipo_doc = data.get("tipoDocumento") or "CC"
        
        identifier = Identifier(
            system="http://www.minsalud.gov.co/identificacion",
            value=numero_doc,
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code=FHIRTransformer._map_document_type(tipo_doc),
                    display=tipo_doc,
                )]
            ),
        )

        nombre_completo = data.get("nombreCompleto")
        if not nombre_completo:
            nombre_completo = f"{data.get('nombres', '')} {data.get('apellidos', '')}".strip() or "Desconocido"
            
        name = HumanName(text=nombre_completo, use="official")

        address = Address(
            use="home",
            country=data.get("paisResidencia") or "Colombia",
            city=FHIRTransformer._get_city_name(data.get("municipioResidencia") or "00000"),
            extension=[
                Extension(
                    url="http://hl7.org/fhir/StructureDefinition/iso21090-SC-coding",
                    valueCoding=Coding(
                        system="https://www.dane.gov.co/divipola",
                        code=data.get("municipioResidencia") or "00000",
                    ),
                )
            ],
        )

        patient = Patient(
            identifier=[identifier],
            name=[name],
            gender=FHIRTransformer._map_gender(data.get("sexo") or data.get("genero")),
            birthDate=str(data.get("fechaNacimiento") or data.get("fecha_nacimiento") or "1900-01-01"),
            address=[address],
        )

        extensions = []

        if data.get("paisNacionalidad"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-nationality",
                extension=[
                    Extension(
                        url="code",
                        valueCodeableConcept=CodeableConcept(
                            coding=[Coding(
                                system="urn:iso:std:iso:3166",
                                code=data["paisNacionalidad"],
                            )]
                        ),
                    )
                ],
            ))

        if data.get("ocupacion"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-occupation",
                valueString=data["ocupacion"],
            ))

        if data.get("etnia") and data["etnia"] != "Ninguna":
            extensions.append(Extension(
                url="http://hl7.org/fhir/us/core/StructureDefinition/us-core-ethnicity",
                valueCodeableConcept=CodeableConcept(text=data["etnia"]),
            ))

        if data.get("categoriaDiscapacidad"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-disability",
                valueCodeableConcept=CodeableConcept(text=data["categoriaDiscapacidad"]),
            ))

        if data.get("genero"):
            extensions.append(Extension(
                url="http://hl7.org/fhir/StructureDefinition/patient-genderIdentity",
                valueCodeableConcept=CodeableConcept(text=data["genero"]),
            ))

        if extensions:
            patient.extension = extensions

        return patient

    @staticmethod
    def _map_document_type(tipo: str) -> str:
        mapping = {
            "CC": "DL",
            "TI": "PPN",
            "CE": "PPN",
            "PA": "PPN",
            "RC": "MR",
            "MS": "AN",
            "AS": "AN",
        }
        return mapping.get(tipo, "DL")

    @staticmethod
    def _map_gender(gender_str: str) -> str:
        if not gender_str:
            return "unknown"
            
        g = gender_str.strip().lower()
        if g in ["m", "masculino", "male"]:
            return "male"
        elif g in ["f", "femenino", "female"]:
            return "female"
        elif g in ["otro", "other", "o"]:
            return "other"
            
        return "unknown"

    @staticmethod
    def _get_city_name(codigo_dane: str) -> str:
        cities = {
            "11001": "Bogotá D.C.",
            "05001": "Medellín",
            "76001": "Cali",
            "08001": "Barranquilla",
            "13001": "Cartagena",
            "68001": "Bucaramanga",
            "66001": "Pereira",
            "17001": "Manizales",
            "50001": "Villavicencio",
        }
        return cities.get(codigo_dane, "Desconocida")
