from fastapi import FastAPI, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pydantic import BaseModel
import json
import os
import time
import uuid

from backend.models import PatientInput, TriageResult, Vitals, PatientUpdatePayload
from backend.security.rbac import get_current_role, require_clinician_role, get_hospital_code
from backend.security.pii_masker import mask_name
from backend.config.profile_manager import profile_manager

from backend.triage_engine.triage_explanation import perform_triage
from backend.queue.queue_monitor import queue_manager, QueueItem
from backend.audit.audit_logger import audit_logger, AuditEvent
from backend.ml.predictor import predict_triage
from backend.ml.reconciler import reconcile
from backend.simulation.patient_generator import generate_patient
from backend.simulation.surge_simulator import create_surge_patients
from backend.simulation.deterioration_simulator import simulate_deterioration
from backend.routers import fhir, ingestion, auth_router
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global supabase_client
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
            # Close existing active sessions
            supabase_client.table("sessions").update({"status": "closed", "closed_at": "now()"}).eq("status", "active").execute()
            # Start new session
            res = supabase_client.table("sessions").insert({"status": "active"}).execute()
            session_id = res.data[0]['id']
            queue_manager.set_session(session_id)
            audit_logger.logs.clear()
            print(f"🚀 Started new DB session: {session_id}")
        except Exception as e:
            print(f"Supabase connection failed: {e}")
    else:
        print("Warning: Supabase credentials missing.")
        
    yield
    
    if supabase_client and getattr(queue_manager, 'active_session_id', None):
        try:
            supabase_client.table("sessions").update({"status": "closed", "closed_at": "now()"}).eq("id", queue_manager.active_session_id).execute()
            print(f"🛑 Closed DB session: {queue_manager.active_session_id}")
        except Exception as e:
            pass

app = FastAPI(title="PatientTriage.ai API — Stage 2", lifespan=lifespan)

app.include_router(fhir.router)
app.include_router(auth_router.router)
app.include_router(ingestion.router)

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
    place_before_patient_id: Optional[str] = None
    place_after_patient_id: Optional[str] = None

class VitalsUpdateRequest(BaseModel):
    patient_id: str
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
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

from backend.services.triage_service import full_triage_pipeline

# ─── API Endpoints ─────────────────────────────────────────────────────────────

@app.get("/api/config/profiles")
def get_profiles():
    """Returns all available hospital configuration profiles."""
    return {
        "active_id": profile_manager.active_profile_id,
        "profiles": profile_manager.get_all_profiles()
    }

@app.post("/api/config/profile/{profile_id}")
def set_profile(profile_id: str):
    """Sets the active hospital configuration profile."""
    if profile_manager.set_active_profile(profile_id):
        # Force a queue re-evaluation using the new profile's SLAs
        queue_manager._check_reassessments()
        return {"status": "success", "active_profile": profile_manager.get_active_profile()}
    raise HTTPException(status_code=404, detail="Profile not found")

@app.post("/api/triage", response_model=TriageResult)
def submit_patient(patient: PatientInput, hospital_code: str = Depends(get_hospital_code)):
    """Submit a patient for triage (raw JSON)."""
    result = full_triage_pipeline(patient)
    queue_manager.add_patient(patient, result, hospital_code=hospital_code)
    return result

@app.post("/api/patient", response_model=TriageResult)
def add_patient_from_form(form: PatientFormRequest, hospital_code: str = Depends(get_hospital_code)):
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
    queue_manager.add_patient(patient, result, hospital_code=hospital_code)
    return result

@app.get("/api/queue", response_model=List[QueueItem])
def get_queue(role: str = Depends(get_current_role), hospital_code: str = Depends(get_hospital_code)):
    """Get all patients in the waiting queue, sorted by priority. Scrubs clinical data for RECEPTIONIST."""
    items = queue_manager.get_queue(hospital_code=hospital_code)
    if role == "RECEPTIONIST":
        scrubbed = []
        for item in items:
            m_item = item.model_copy(deep=True) if hasattr(item, 'model_copy') else item.copy(deep=True)
            m_item.patient.vitals = Vitals() # empty vitals
            m_item.triage_result.reasons = []
            m_item.triage_result.feature_importances = None
            m_item.triage_result.ml_confidence = None
            m_item.triage_result.rules_priority = ""
            m_item.initial_vitals = None
            scrubbed.append(m_item)
        return scrubbed
    elif role != "CLINICIAN":
        masked_items = []
        for item in items:
            m_item = item.model_copy(deep=True) if hasattr(item, 'model_copy') else item.copy(deep=True)
            m_item.patient.name = mask_name(m_item.patient.name)
            masked_items.append(m_item)
        return masked_items
    return items

@app.get("/api/completed", response_model=List[QueueItem])
def get_completed_queue(role: str = Depends(get_current_role), hospital_code: str = Depends(get_hospital_code)):
    """Get all completed/discharged patients. Scrubs clinical data for RECEPTIONIST."""
    items = queue_manager.get_completed_queue(hospital_code=hospital_code)
    if role == "RECEPTIONIST":
        scrubbed = []
        for item in items:
            m_item = item.model_copy(deep=True) if hasattr(item, 'model_copy') else item.copy(deep=True)
            m_item.patient.vitals = Vitals()
            m_item.triage_result.reasons = []
            m_item.triage_result.feature_importances = None
            m_item.triage_result.ml_confidence = None
            m_item.triage_result.rules_priority = ""
            m_item.initial_vitals = None
            scrubbed.append(m_item)
        return scrubbed
    elif role != "CLINICIAN":
        masked_items = []
        for item in items:
            m_item = item.model_copy(deep=True) if hasattr(item, 'model_copy') else item.copy(deep=True)
            m_item.patient.name = mask_name(m_item.patient.name)
            masked_items.append(m_item)
        return masked_items
    return items

@app.post("/api/completed/{patient_id}/archive")
def archive_completed_patient(patient_id: str, hospital_code: str = Depends(get_hospital_code)):
    """Archive a completed patient (removes them from completed list)."""
    if not queue_manager.has_patient(patient_id, hospital_code=hospital_code):
        raise HTTPException(status_code=404, detail="Patient not found")
    queue_manager.archive_patient(patient_id)
    return {"status": "Patient archived", "patient_id": patient_id}

@app.post("/api/queue/vitals")
def update_vitals(req: VitalsUpdateRequest, role: str = Depends(require_clinician_role), hospital_code: str = Depends(get_hospital_code)):
    """Update a patient's vitals (simulates deterioration or re-measurement)."""
    if not queue_manager.has_patient(req.patient_id, hospital_code=hospital_code):
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    queue_manager.update_vitals(
        req.patient_id,
        new_hr=req.heart_rate,
        new_spo2=req.spo2,
        new_temp=req.temperature,
        new_rr=req.respiratory_rate,
        new_gcs=req.gcs,
        new_bp=req.blood_pressure
    )

    # If worsening detected, perform full re-triage
    item = queue_manager.get_patient(req.patient_id, hospital_code=hospital_code)
    if item and item.escalation_required:
        old_priority = item.triage_result.priority
        new_result = full_triage_pipeline(item.patient)
        queue_manager.retriage_patient(req.patient_id, new_result)
        audit_logger.log_retriage(
            req.patient_id, old_priority, new_result.priority,
            "VITALS_UPDATE", new_result.confidence
        )
        return {"status": "success", "escalation_triggered": True}

    return {"status": "success", "escalation_triggered": False}

@app.post("/api/override")
def override_priority(req: OverrideRequest, role: str = Depends(require_clinician_role), hospital_code: str = Depends(get_hospital_code)):
    """Clinician overrides the system's recommended priority."""
    if not queue_manager.has_patient(req.patient_id, hospital_code=hospital_code):
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    old_prio = queue_manager.override_patient(
        patient_id=req.patient_id,
        new_priority=req.new_priority,
        reason=req.reason,
        place_before_id=req.place_before_patient_id,
        place_after_id=req.place_after_patient_id
    )

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
    """Start a 3× surge simulation — uses dynamic capacity limits."""
    trigger_capacity = profile_manager.get_surge_trigger_capacity()
    patients = create_surge_patients(multiplier=3, base_count=trigger_capacity)
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
    audit_logger.log_surge("STOP", len(queue_manager.get_queue()))
    return {"status": "Surge mode deactivated", "surge_mode": False}

@app.post("/api/surge")
def simulate_surge_legacy():
    """Legacy surge endpoint — loads seed patients for backward compatibility."""
    seed_path = os.path.join(os.path.dirname(__file__), '..', 'patient_data', 'seed', 'simulated_patients.json')
    try:
        with open(seed_path, 'r') as f:
            patients_data = json.load(f)
            for p_data in patients_data:
                # Ensure unique ID to avoid PK collisions from prior sessions
                p_data['id'] = f"{p_data.get('id', 'PT')}_{uuid.uuid4().hex[:6].upper()}"
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
    current_queue = {item.patient.id: item for item in queue_manager.get_queue()}
    deteriorated_ids = simulate_deterioration(current_queue, percentage=0.15)

    # Re-triage each deteriorated patient
    retriaged = []
    for pid in deteriorated_ids:
        item = current_queue.get(pid)
        if item:
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
def discharge_patient(patient_id: str, hospital_code: str = Depends(get_hospital_code)):
    """Remove a patient from the queue (discharge)."""
    if not queue_manager.has_patient(patient_id, hospital_code=hospital_code):
        raise HTTPException(status_code=404, detail="Patient not found in queue")

    queue_manager.remove_patient(patient_id)
    audit_logger.log_discharge(patient_id)
    return {"status": "Patient discharged", "patient_id": patient_id}

@app.post("/api/clear")
def clear_state(hospital_code: str = Depends(get_hospital_code)):
    """Clear all state (reset queue, audit logs, surge mode)."""
    queue_manager.clear_all(hospital_code=hospital_code)
    audit_logger.logs.clear()
    queue_manager.deactivate_surge()
    return {"status": "cleared"}

from backend.nlp_parser import extract_vitals_from_text

class ChatVitalsRequest(BaseModel):
    text: str

@app.get("/api/chat/patients")
def search_patients_for_chat(name: str):
    """Search for patients in the active queue by name."""
    name_lower = name.lower()
    matches = []
    for item in queue_manager.get_queue():
        if name_lower in item.patient.name.lower() or name_lower in item.patient.id.lower():
            matches.append({
                "id": item.patient.id,
                "name": item.patient.name,
                "age": item.patient.age,
                "gender": item.patient.gender
            })
    return {"matches": matches}

@app.post("/api/chat/extract_vitals")
def chat_extract_vitals(req: ChatVitalsRequest):
    """Extract vitals JSON from natural language text using the rule-based parser."""
    try:
        extracted = extract_vitals_from_text(req.text)
        return {"extracted": extracted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend

@app.patch("/api/queue/{patient_id}/update")
def update_patient_details(patient_id: str, req: PatientUpdatePayload, hospital_code: str = Depends(get_hospital_code)):
    """Update general patient details and trigger a re-triage."""
    item = queue_manager.get_patient(patient_id, hospital_code=hospital_code)
    if not item:
        raise HTTPException(status_code=404, detail="Patient not found in active queue")
        
    patient = item.patient
    old_priority = item.triage_result.priority
    changed = False

    update_data = req.model_dump(exclude_unset=True) if hasattr(req, 'model_dump') else req.dict(exclude_unset=True)
    vitals_keys = {'heart_rate', 'blood_pressure', 'spo2', 'temperature', 'respiratory_rate', 'gcs', 'pain_scale'}
    
    for key, value in update_data.items():
        if key in vitals_keys:
            if getattr(patient.vitals, key, None) != value:
                setattr(patient.vitals, key, value)
                changed = True
        else:
            if getattr(patient, key, None) != value:
                setattr(patient, key, value)
                changed = True
        
    if changed:
        new_result = full_triage_pipeline(patient)
        queue_manager.retriage_patient(patient_id, new_result, new_patient_data=patient)
        audit_logger.log_retriage(
            patient_id, old_priority, new_result.priority,
            "DETAILS_UPDATED", new_result.confidence
        )
        return {"status": "success", "retriaged": True, "new_priority": new_result.priority}
        
    return {"status": "success", "retriaged": False, "message": "No fields changed"}

from fastapi.responses import FileResponse

@app.get("/hospitals")
def get_hospitals_page():
    """Serve the Hospital Admin Portal"""
    return FileResponse("frontend/hospital_portal.html")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
