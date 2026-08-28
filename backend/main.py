from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import time
import uuid

from backend.models import PatientInput, TriageResult, Vitals
from backend.triage_engine.triage_explanation import perform_triage
from backend.queue.queue_monitor import queue_manager, QueueItem
from backend.audit.audit_logger import audit_logger, AuditEvent
from backend.ml.predictor import predict_triage
from backend.ml.reconciler import reconcile
from backend.simulation.patient_generator import generate_patient
from backend.simulation.surge_simulator import create_surge_patients
from backend.simulation.deterioration_simulator import simulate_deterioration

app = FastAPI(title="PatientTriage.ai API — Stage 2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Request/Response models ───────────────────────────────────────────────────

class OverrideRequest(BaseModel):
    patient_id: str
    new_priority: str
    reason: str

class VitalsUpdateRequest(BaseModel):
    patient_id: str
    heart_rate: Optional[int] = None
    spo2: Optional[int] = None
    temperature: Optional[float] = None
    respiratory_rate: Optional[int] = None
    gcs: Optional[int] = None

class PatientFormRequest(BaseModel):
    """For adding a patient via the UI form."""
    name: str
    age: int
    gender: str
    chief_complaint: str
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    gcs: Optional[int] = None
    pain_scale: Optional[int] = None
    history_available: bool = False
    medical_history: List[str] = []
    observed_signs: List[str] = []
    arrival_mode: Optional[str] = None
    symptoms: List[str] = []

# ─── Helper: full triage pipeline (rules + ML + reconcile) ─────────────────────

def full_triage_pipeline(patient: PatientInput) -> TriageResult:
    """
    Run the complete hybrid triage pipeline:
    1. Deterministic rules engine → rules_priority
    2. ML model → ml_priority (advisory)
    3. Reconciler → final priority (ML can escalate, never downgrade)
    4. Log everything to audit trail
    """
    # Step 1: Rules-based triage
    result = perform_triage(patient)

    # Step 2: ML prediction
    ml_priority, ml_confidence, feature_importances = predict_triage(patient)

    # Step 3: Reconcile rules + ML
    final_priority, source, disagreement = reconcile(
        result.priority, result.confidence, ml_priority, ml_confidence
    )

    # Update result with ML and reconciliation data
    result.ml_priority = ml_priority
    result.ml_confidence = ml_confidence
    result.feature_importances = feature_importances
    result.source = source
    result.disagreement = disagreement
    result.priority = final_priority

    # Step 4: Audit logging
    audit_logger.log_triage(
        patient.id, final_priority, result.confidence,
        source, result.rules_priority, ml_priority
    )

    # Log disagreement separately if it occurred
    if disagreement and source in ("ML_ESCALATED", "RULES_FLOOR"):
        audit_logger.log_disagreement(
            patient.id, result.rules_priority,
            ml_priority, final_priority, source
        )

    return result

# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.post("/api/triage", response_model=TriageResult)
def submit_patient(patient: PatientInput):
    """Submit a patient for triage (raw JSON)."""
    result = full_triage_pipeline(patient)
    queue_manager.add_patient(patient, result)
    return result

@app.post("/api/patient", response_model=TriageResult)
def add_patient_from_form(form: PatientFormRequest):
    """Add a new patient from the UI form. Auto-generates ID."""
    patient_id = f"PT_{uuid.uuid4().hex[:6].upper()}"

    # Parse blood pressure into structured fields
    sys_bp = None
    dia_bp = None
    if form.blood_pressure:
        try:
            parts = form.blood_pressure.split('/')
            sys_bp = int(parts[0].strip())
            dia_bp = int(parts[1].strip())
        except (ValueError, IndexError):
            pass

    patient = PatientInput(
        id=patient_id,
        name=form.name,
        age=form.age,
        gender=form.gender,
        chief_complaint=form.chief_complaint,
        vitals=Vitals(
            heart_rate=form.heart_rate,
            blood_pressure=form.blood_pressure,
            systolic_bp=sys_bp,
            diastolic_bp=dia_bp,
            respiratory_rate=form.respiratory_rate,
            temperature=form.temperature,
            spo2=form.spo2,
            gcs=form.gcs,
            pain_scale=form.pain_scale
        ),
        history_available=form.history_available,
        medical_history=form.medical_history,
        observed_signs=form.observed_signs,
        arrival_mode=form.arrival_mode,
        symptoms=form.symptoms
    )

    result = full_triage_pipeline(patient)
    queue_manager.add_patient(patient, result)
    return result

@app.get("/api/queue", response_model=List[QueueItem])
def get_queue():
    """Get all patients in the waiting queue, sorted by priority."""
    return queue_manager.get_queue()

@app.post("/api/queue/vitals")
def update_vitals(req: VitalsUpdateRequest):
    """Update a patient's vitals (simulates deterioration or re-measurement)."""
    if req.patient_id not in queue_manager.queue:
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    queue_manager.update_vitals(
        req.patient_id,
        new_hr=req.heart_rate,
        new_spo2=req.spo2,
        new_temp=req.temperature,
        new_rr=req.respiratory_rate,
        new_gcs=req.gcs
    )

    # If worsening detected, perform full re-triage
    item = queue_manager.queue[req.patient_id]
    if item.escalation_required:
        old_priority = item.triage_result.priority
        new_result = full_triage_pipeline(item.patient)
        queue_manager.retriage_patient(req.patient_id, new_result)
        audit_logger.log_retriage(
            req.patient_id, old_priority, new_result.priority,
            "VITALS_UPDATE", new_result.confidence
        )

    return {"status": "success", "escalation_triggered": item.escalation_required}

@app.post("/api/override")
def override_priority(req: OverrideRequest):
    """Clinician overrides the system's recommended priority."""
    if req.patient_id not in queue_manager.queue:
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    item = queue_manager.queue[req.patient_id]
    old_prio = item.triage_result.priority

    # Apply override
    item.triage_result.priority = req.new_priority
    item.triage_result.reasons.append(f"Clinician Override: {req.reason}")
    item.triage_result.source = "CLINICIAN_OVERRIDE"

    # Audit log
    audit_logger.log_override(req.patient_id, old_prio, req.new_priority, req.reason)

    return {"status": "success", "old_priority": old_prio, "new_priority": req.new_priority}

@app.get("/api/audit", response_model=List[AuditEvent])
def get_audit_logs(event_type: Optional[str] = None):
    """Get audit logs, optionally filtered by event type."""
    return audit_logger.get_logs(event_type=event_type)

@app.get("/api/stats")
def get_stats():
    """Dashboard statistics."""
    queue_stats = queue_manager.get_stats()
    audit_stats = audit_logger.get_stats()
    return {
        "queue": queue_stats,
        "audit": audit_stats
    }

@app.post("/api/surge/start")
def start_surge():
    """Start a 3× surge simulation — generates ~64 new patients."""
    patients = create_surge_patients(multiplier=3, base_count=20)
    queue_manager.activate_surge()

    for patient in patients:
        result = full_triage_pipeline(patient)
        queue_manager.add_patient(patient, result)

    audit_logger.log_surge("START", len(patients))

    return {
        "status": "Surge mode activated",
        "patients_added": len(patients),
        "surge_mode": True
    }

@app.post("/api/surge/stop")
def stop_surge():
    """Stop surge mode — restore normal thresholds."""
    queue_manager.deactivate_surge()
    audit_logger.log_surge("STOP", len(queue_manager.queue))
    return {"status": "Surge mode deactivated", "surge_mode": False}

@app.post("/api/surge")
def simulate_surge_legacy():
    """Legacy surge endpoint — loads seed patients for backward compatibility."""
    seed_path = os.path.join(os.path.dirname(__file__), '..', 'patient_data', 'seed', 'simulated_patients.json')
    try:
        with open(seed_path, 'r') as f:
            patients_data = json.load(f)
            for p_data in patients_data:
                patient = PatientInput(**p_data)
                result = full_triage_pipeline(patient)
                queue_manager.add_patient(patient, result)

        queue_manager.activate_surge()
        audit_logger.log_surge("LEGACY_START", len(patients_data))
        return {"status": "Surge mode activated (seed patients)", "patients_added": len(patients_data)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/simulate/deteriorate")
def simulate_deterioration_endpoint():
    """Simulate deterioration in waiting patients."""
    deteriorated_ids = simulate_deterioration(queue_manager.queue, percentage=0.15)

    # Re-triage each deteriorated patient
    retriaged = []
    for pid in deteriorated_ids:
        if pid in queue_manager.queue:
            item = queue_manager.queue[pid]
            old_priority = item.triage_result.priority
            new_result = full_triage_pipeline(item.patient)
            queue_manager.retriage_patient(pid, new_result)
            audit_logger.log_deterioration(pid, ["vitals_worsened"])
            audit_logger.log_retriage(pid, old_priority, new_result.priority,
                                      "DETERIORATION_SIM", new_result.confidence)
            retriaged.append({
                "patient_id": pid,
                "old_priority": old_priority,
                "new_priority": new_result.priority
            })

    return {
        "status": "Deterioration simulated",
        "patients_affected": len(deteriorated_ids),
        "retriaged": retriaged
    }

@app.post("/api/queue/{patient_id}/discharge")
def discharge_patient(patient_id: str):
    """Remove a patient from the queue (discharge)."""
    if patient_id not in queue_manager.queue:
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    queue_manager.remove_patient(patient_id)
    audit_logger.log_discharge(patient_id)
    return {"status": "Patient discharged", "patient_id": patient_id}

@app.post("/api/clear")
def clear_state():
    """Clear all state (reset queue, audit logs, surge mode)."""
    queue_manager.queue.clear()
    audit_logger.logs.clear()
    queue_manager.deactivate_surge()
    return {"status": "cleared"}

# Mount frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
