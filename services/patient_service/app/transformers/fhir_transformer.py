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
        identifier = Identifier(
            system="http://www.minsalud.gov.co/identificacion",
            value=data["numeroDocumento"],
            type=CodeableConcept(
                coding=[Coding(
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code=FHIRTransformer._map_document_type(data["tipoDocumento"]),
                    display=data["tipoDocumento"],
                )]
            ),
        )

        name = HumanName(text=data["nombreCompleto"], use="official")

        address = Address(
            use="home",
            country=data["paisResidencia"],
            city=FHIRTransformer._get_city_name(data["municipioResidencia"]),
            extension=[
                Extension(
                    url="http://hl7.org/fhir/StructureDefinition/iso21090-SC-coding",
                    valueCoding=Coding(
                        system="https://www.dane.gov.co/divipola",
                        code=data["municipioResidencia"],
                    ),
                )
            ],
        )

        patient = Patient(
            identifier=[identifier],
            name=[name],
            gender=data["sexo"],
            birthDate=str(data["fechaNacimiento"]),
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
