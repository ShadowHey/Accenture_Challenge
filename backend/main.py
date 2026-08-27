from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import time

from backend.models import PatientInput, TriageResult
from backend.triage_engine.triage_explanation import perform_triage
from backend.queue.queue_monitor import queue_manager, QueueItem
from backend.audit.audit_logger import audit_logger, OverrideRecord

app = FastAPI(title="PatientTriage.ai API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models for specific endpoints
class OverrideRequest(BaseModel):
    patient_id: str
    new_priority: str
    reason: str

class VitalsUpdateRequest(BaseModel):
    patient_id: str
    heart_rate: Optional[int] = None
    spo2: Optional[int] = None

@app.post("/api/triage", response_model=TriageResult)
def submit_patient(patient: PatientInput):
    result = perform_triage(patient)
    queue_manager.add_patient(patient, result)
    return result

@app.get("/api/queue", response_model=List[QueueItem])
def get_queue():
    return queue_manager.get_queue()

@app.post("/api/queue/vitals")
def update_vitals(req: VitalsUpdateRequest):
    queue_manager.update_vitals(req.patient_id, req.heart_rate, req.spo2)
    return {"status": "success"}

@app.post("/api/override")
def override_priority(req: OverrideRequest):
    if req.patient_id not in queue_manager.queue:
        raise HTTPException(status_code=404, detail="Patient not found in queue")
    
    item = queue_manager.queue[req.patient_id]
    old_prio = item.triage_result.priority
    item.triage_result.priority = req.new_priority
    item.triage_result.reasons.append(f"Clinician Override: {req.reason}")
    
    audit_logger.log_override(req.patient_id, old_prio, req.new_priority, req.reason)
    return {"status": "success", "new_priority": req.new_priority}

@app.get("/api/audit", response_model=List[OverrideRecord])
def get_audit_logs():
    return audit_logger.get_logs()

@app.post("/api/surge")
def simulate_surge():
    # Loads the simulated patients and inserts them to simulate a 3x surge
    seed_path = os.path.join(os.path.dirname(__file__), '..', 'patient_data', 'seed', 'simulated_patients.json')
    try:
        with open(seed_path, 'r') as f:
            patients = json.load(f)
            # Add them all to the queue
            for p_data in patients:
                patient = PatientInput(**p_data)
                result = perform_triage(patient)
                queue_manager.add_patient(patient, result)
        
        # Lower the wait threshold to simulate congestion and faster reassessment needs
        queue_manager.wait_threshold = 10 
        return {"status": "Surge mode activated", "patients_added": len(patients)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/clear")
def clear_state():
    queue_manager.queue.clear()
    audit_logger.logs.clear()
    queue_manager.wait_threshold = 60
    return {"status": "cleared"}

# Mount frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
