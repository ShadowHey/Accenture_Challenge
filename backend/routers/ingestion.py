from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.models import HistoricalRecord
from backend.security.auth import verify_hospital
from backend.queue.queue_monitor import queue_manager
import uuid

router = APIRouter(prefix="/api/v1/hospital", tags=["hospital"])

@router.post("/records")
def ingest_historical_records(
    records: List[HistoricalRecord], 
    hospital: dict = Depends(verify_hospital)
):
    """
    Ingest historical patient records from an authenticated hospital.
    """
    if not queue_manager.supabase:
        raise HTTPException(status_code=500, detail="Database not initialized")
        
    inserted_count = 0
    errors = []
    
    # Process in batches or one by one
    for record in records:
        try:
            payload = {
                "id": str(uuid.uuid4()),
                "hospital_id": hospital['id'],
                "patient_name": record.name,
                "age": record.age,
                "gender": record.gender,
                "chief_complaint": record.chief_complaint,
                "vitals": record.vitals or {},
                "medical_history": record.medical_history or [],
                "observed_signs": record.observed_signs or [],
                "visit_date": record.visit_date,
                "discharge_status": record.discharge_status,
                "raw_data": record.model_dump() if hasattr(record, 'model_dump') else record.dict()
            }
            queue_manager.supabase.table('historical_records').insert(payload).execute()
            inserted_count += 1
        except Exception as e:
            errors.append({"record": record.name, "error": str(e)})
            
    response = {
        "status": "success",
        "message": f"Successfully ingested {inserted_count} records for {hospital['name']}.",
        "records_inserted": inserted_count
    }
    
    if errors:
        response["errors"] = errors
        
    return response
