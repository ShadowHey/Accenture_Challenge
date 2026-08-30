import os

# 1. Update backend/routers/auth_router.py
auth_router_path = "/Users/dhruv/Desktop/Projects/patient_triage.ai/backend/routers/auth_router.py"
with open(auth_router_path, 'r') as f:
    auth_content = f.read()

auth_replacement = """import os
from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client
import bcrypt

from backend.security.hospital_auth import authenticate_user, create_session_token, invalidate_token, get_current_user

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

router = APIRouter(prefix="/api/auth", tags=["auth"])

def get_supabase_client():
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    return create_client(SUPABASE_URL, SUPABASE_KEY)

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    hospital_code: str
    password: str

@router.post("/register")
def register(req: RegisterRequest):
    supabase = get_supabase_client()
    res = supabase.table("hospitals").select("*").eq("hospital_code", req.hospital_code).execute()
    if res.data:
        raise HTTPException(status_code=400, detail="Hospital code already exists")
    
    hashed = bcrypt.hashpw(req.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    supabase.table("hospitals").insert({
        "name": req.name,
        "hospital_code": req.hospital_code,
        "password_hash": hashed
    }).execute()
    return {"status": "success", "message": "Hospital registered successfully"}

@router.post("/login")
def login(req: LoginRequest):
    try:
        user_info = authenticate_user(req.username, req.password)
        token = create_session_token(user_info["username"], user_info["role"], user_info["hospital_code"])
        
        supabase = get_supabase_client()
        hospital_name = "Unknown Hospital"
        try:
            res = supabase.table("hospitals").select("name").eq("hospital_code", user_info["hospital_code"]).execute()
            if res.data:
                hospital_name = res.data[0]["name"]
        except Exception:
            pass
            
        return {
            "token": token,
            "role": user_info["role"],
            "hospital_code": user_info["hospital_code"],
            "hospital_name": hospital_name,
            "username": user_info["username"]
        }
    except HTTPException:
        supabase = get_supabase_client()
        res = supabase.table("hospitals").select("*").eq("hospital_code", req.username).execute()
        if not res.data:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        hosp = res.data[0]
        if not bcrypt.checkpw(req.password.encode('utf-8'), hosp['password_hash'].encode('utf-8')):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        token = create_session_token(req.username, "HOSPITAL_ADMIN", req.username)
        return {
            "token": token,
            "role": "HOSPITAL_ADMIN",
            "hospital_code": req.username,
            "hospital_name": hosp["name"],
            "username": req.username
        }
"""
# Since auth_router has /logout and /me, we should retain them
auth_tail = """
@router.post("/logout")
def logout(authorization: Optional[str] = Header(None)):
    if authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            invalidate_token(parts[1])
    return {"status": "logged_out"}

@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    supabase = get_supabase_client()
    hospital_name = "Unknown Hospital"
    try:
        res = supabase.table("hospitals").select("name").eq("hospital_code", user["hospital_code"]).execute()
        if res.data:
            hospital_name = res.data[0]["name"]
    except Exception:
        pass
        
    return {
        "username": user["username"],
        "role": user["role"],
        "hospital_code": user["hospital_code"],
        "hospital_name": hospital_name
    }
"""
with open(auth_router_path, 'w') as f:
    f.write(auth_replacement + auth_tail)


# 2. Update backend/routers/fhir.py
fhir_path = "/Users/dhruv/Desktop/Projects/patient_triage.ai/backend/routers/fhir.py"
with open(fhir_path, 'r') as f:
    fhir_content = f.read()

if "/historical" not in fhir_content:
    new_fhir_head = """from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
import os
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

"""
    idx = fhir_content.find('@router.post("/Bundle")')
    if idx != -1:
        with open(fhir_path, 'w') as f:
            f.write(new_fhir_head + fhir_content[idx:])


# 3. Update backend/services/triage_service.py
triage_path = "/Users/dhruv/Desktop/Projects/patient_triage.ai/backend/services/triage_service.py"
with open(triage_path, 'r') as f:
    triage_content = f.read()

if "historical_records" not in triage_content:
    new_triage = triage_content.replace(
"""def full_triage_pipeline(patient: PatientInput) -> TriageResult:""",
"""import os
from supabase import create_client

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def full_triage_pipeline(patient: PatientInput) -> TriageResult:
    # Auto-fill medical history if missing
    if not patient.medical_history or not patient.history_available:
        try:
            if SUPABASE_URL and SUPABASE_KEY:
                supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
                res = supabase.table("historical_records").select("medical_history, chief_complaint").ilike("patient_name", patient.name).eq("gender", patient.gender).execute()
                if res.data:
                    past_conditions = set(patient.medical_history or [])
                    for record in res.data:
                        if record.get("medical_history"):
                            past_conditions.update(record["medical_history"])
                        if record.get("chief_complaint") and record.get("chief_complaint") != "Referred via FHIR Integration":
                            past_conditions.add(record["chief_complaint"])
                    if past_conditions:
                        patient.medical_history = list(past_conditions)
                        patient.history_available = True
                        print(f"Auto-filled medical history for {patient.name}: {patient.medical_history}")
        except Exception as e:
            print(f"Error fetching historical records: {e}")
"""
    )
    with open(triage_path, 'w') as f:
        f.write(new_triage)

print("Backend files updated successfully.")
