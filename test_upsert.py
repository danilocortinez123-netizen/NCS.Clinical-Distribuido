import requests
import uuid
import time

def run_test():
    print("Testing UPSERT and Deduplication via API...")
    
    patient_id = f"P-test-{uuid.uuid4().hex[:4]}"
    
    payload = {
        "documento": "DOC-12345",
        "target_sede": "SedeTest",
        "source": "SourceA",
        "fhir_resource": {
            "resourceType": "Patient",
            "id": patient_id,
            "identifier": [{"value": "DOC-12345"}],
            "name": [{"given": ["TestName"], "family": "TestFamily"}],
            "clinical_records": [
                {
                    "encounter": {"id": "enc-1", "status": "finished"},
                    "observation": {"id": "obs-1", "value": "test1"},
                    "condition": {},
                    "medication_request": {}
                }
            ]
        }
    }
    
    print("\nImporting first time...")
    res = requests.post("http://localhost:8002/api/v1/patient/import", json=payload)
    print("Result 1:", res.json())
    
    time.sleep(1)
    
    print("\nImporting second time (same records)...")
    res2 = requests.post("http://localhost:8002/api/v1/patient/import", json=payload)
    print("Result 2:", res2.json())
    
    time.sleep(1)
    
    print("\nImporting third time (new record)...")
    payload["fhir_resource"]["clinical_records"].append({
        "encounter": {"id": "enc-2", "status": "finished"},
        "observation": {"id": "obs-2", "value": "test2"},
        "condition": {},
        "medication_request": {}
    })
    res3 = requests.post("http://localhost:8002/api/v1/patient/import", json=payload)
    print("Result 3:", res3.json())
    
    time.sleep(1)
    print("\nCheck the DB manually to verify deduplication. But message should say 'Paciente actualizado' for 2 and 3.")

if __name__ == "__main__":
    run_test()
