import httpx
from fhir.resources.patient import Patient
from typing import Any, Optional


class FHIRClient:

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json",
        }

    async def create_patient(self, patient: Patient) -> dict[str, Any]:
        patient_json = patient.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/Patient",
                content=patient_json,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_patient(self, patient_id: str) -> Optional[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/Patient/{patient_id}",
                headers=self.headers,
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def search_by_identifier(self, identifier: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/Patient",
                params={"identifier": identifier},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def search_resource(self, resource_type: str, params: dict) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/{resource_type}",
                params=params,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def update_patient(self, patient_id: str, patient: Patient) -> dict[str, Any]:
        patient_json = patient.json()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                f"{self.base_url}/Patient/{patient_id}",
                content=patient_json,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def delete_patient(self, patient_id: str) -> bool:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{self.base_url}/Patient/{patient_id}",
                headers=self.headers,
            )
            response.raise_for_status()
            return True

    async def list_patients(self, page: int = 1, size: int = 10) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/Patient",
                params={"_count": size, "_page": page},
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    async def check_health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{self.base_url}/metadata",
                headers={"Accept": "application/fhir+json"},
            )
            response.raise_for_status()
            return response.json()
