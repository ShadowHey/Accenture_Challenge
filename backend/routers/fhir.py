from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from pydantic import BaseModel, HttpUrl
import os
import httpx
from supabase import create_client

from backend.adapters.fhir_parser import parse_fhir_bundle, FHIRParserError
from backend.models import PatientInput
from backend.services.triage_service import full_triage_pipeline
from backend.queue.queue_monitor import queue_manager
from backend.security.rbac import get_hospital_code

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

router = APIRouter(prefix="/api/fhir", tags=["fhir"])

@router.post("/historical")
def process_historical_fhir_bundle(bundle: Dict[str, Any], hospital_code: str = Depends(get_hospital_code)):
    try:
        parsed_data = parse_fhir_bundle(bundle)
        patient_input = PatientInput(**parsed_data)
        
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        res = supabase.table("hospitals").select("id").eq("hospital_code", hospital_code).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Hospital not found")
        hosp_id = res.data[0]["id"]
        
        record = {
            "hospital_id": hosp_id,
            "patient_name": patient_input.name,
            "age": patient_input.age,
            "gender": patient_input.gender,
            "chief_complaint": patient_input.chief_complaint,
            "vitals": patient_input.vitals.model_dump() if hasattr(patient_input.vitals, 'model_dump') else patient_input.vitals.dict(),
            "medical_history": patient_input.medical_history,
            "observed_signs": patient_input.observed_signs,
            "raw_data": bundle
        }
        supabase.table("historical_records").insert(record).execute()
        
        return {"status": "success", "message": "Historical FHIR data saved successfully"}
    except FHIRParserError as e:
        raise HTTPException(status_code=400, detail=f"FHIR Parsing Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error processing FHIR Bundle: {str(e)}")

@router.post("/Bundle")
def process_fhir_bundle(bundle: Dict[str, Any]):
    """
    Ingests a standard FHIR Bundle containing Patient and Observation resources.
    Translates it into our internal PatientInput model and adds the patient to the queue.
    """
    try:
        # 1. Parse standard FHIR JSON into our internal dictionary format
        parsed_data = parse_fhir_bundle(bundle)
        
        # 2. Convert to Pydantic model
        patient_input = PatientInput(**parsed_data)
        
        # 3. Run the standard triage pipeline
        result = full_triage_pipeline(patient_input)
        
        # 4. Add to queue
        queue_manager.add_patient(patient_input, result)
        
        return {
            "status": "success",
            "message": "FHIR Bundle processed successfully",
            "patient_id": patient_input.id,
            "triage_result": result
        }
    except FHIRParserError as e:
        raise HTTPException(status_code=400, detail=f"FHIR Parsing Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error processing FHIR Bundle: {str(e)}")


class FHIRFetchRequest(BaseModel):
    fhir_url: HttpUrl


@router.post("/fetch-and-submit")
def fetch_and_submit_fhir(request: FHIRFetchRequest, hospital_code: str = Depends(get_hospital_code)):
    """
    Fetches a FHIR Bundle from the provided external URL server-side,
    then parses and stores it as a historical record — no copy-pasting needed.
    """
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(str(request.fhir_url), headers={"Accept": "application/fhir+json"})
            response.raise_for_status()
            bundle = response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Request to FHIR server timed out (10s limit)")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"FHIR server returned error: {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch from FHIR URL: {str(e)}")

    try:
        parsed_data = parse_fhir_bundle(bundle)
        patient_input = PatientInput(**parsed_data)

        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        res = supabase.table("hospitals").select("id").eq("hospital_code", hospital_code).execute()
        if not res.data:
            raise HTTPException(status_code=404, detail="Hospital not found")
        hosp_id = res.data[0]["id"]

        record = {
            "hospital_id": hosp_id,
            "patient_name": patient_input.name,
            "age": patient_input.age,
            "gender": patient_input.gender,
            "chief_complaint": patient_input.chief_complaint,
            "vitals": patient_input.vitals.model_dump() if hasattr(patient_input.vitals, 'model_dump') else patient_input.vitals.dict(),
            "medical_history": patient_input.medical_history,
            "observed_signs": patient_input.observed_signs,
            "raw_data": bundle
        }
        supabase.table("historical_records").insert(record).execute()

        return {"status": "success", "message": "FHIR data fetched from URL and saved successfully"}
    except FHIRParserError as e:
        raise HTTPException(status_code=400, detail=f"FHIR Parsing Error: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Error processing fetched FHIR Bundle: {str(e)}")
