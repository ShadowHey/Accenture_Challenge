import re
from backend.models import PatientInput
from sentence_transformers import SentenceTransformer

# Load the model once at module level to avoid reloading on every request
_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model

FEATURE_NAMES = [
    "age",
    "is_pediatric",
    "is_geriatric",
    "heart_rate",
    "sys_bp",
    "dia_bp",
    "respiratory_rate",
    "temperature",
    "spo2",
    "gcs",
    "pain_scale",
    "history_available",
    "num_medical_conditions",
    "num_observed_signs",
    "arrival_mode_encoded",
    "missing_vitals"
] + [f"emb_{i}" for i in range(384)]

def _parse_bp(patient: PatientInput):
    sys_val = patient.vitals.systolic_bp
    dia_val = patient.vitals.diastolic_bp
    if (sys_val is None or dia_val is None) and patient.vitals.blood_pressure:
        match = re.match(r"(\d+)/(\d+)", patient.vitals.blood_pressure)
        if match:
            if sys_val is None: sys_val = int(match.group(1))
            if dia_val is None: dia_val = int(match.group(2))
    return sys_val or 0, dia_val or 0

def extract_features(patient: PatientInput) -> list:
    age = patient.age
    is_pediatric = 1 if age < 18 else 0
    is_geriatric = 1 if age > 65 else 0

    heart_rate = patient.vitals.heart_rate or 0
    sys_bp, dia_bp = _parse_bp(patient)
    respiratory_rate = patient.vitals.respiratory_rate or 0
    temperature = float(patient.vitals.temperature) if patient.vitals.temperature else 0.0
    spo2 = patient.vitals.spo2 or 0
    gcs = patient.vitals.gcs or 0
    pain_scale = patient.vitals.pain_scale or 0

    history_available = 1 if patient.history_available else 0
    num_medical_conditions = len(patient.medical_history) if patient.medical_history else 0
    num_observed_signs = len(patient.observed_signs) if patient.observed_signs else 0

    arrival_mode = (patient.arrival_mode or "").lower()
    if arrival_mode == "ambulance":
        arrival_mode_encoded = 1
    elif arrival_mode == "helicopter":
        arrival_mode_encoded = 2
    else:
        arrival_mode_encoded = 0

    missing_vitals = 0
    if patient.vitals.heart_rate is None: missing_vitals += 1
    if patient.vitals.blood_pressure is None and patient.vitals.systolic_bp is None: missing_vitals += 1
    if patient.vitals.respiratory_rate is None: missing_vitals += 1
    if patient.vitals.temperature is None: missing_vitals += 1
    if patient.vitals.spo2 is None: missing_vitals += 1

    # Text extraction and encoding
    c_text = (patient.chief_complaint or "").lower()
    s_text = " ".join(patient.observed_signs).lower() if patient.observed_signs else ""
    full_text = f"{c_text} {s_text}".strip()
    
    if not full_text:
        full_text = "unknown"
        
    model = get_model()
    embeddings = model.encode([full_text])[0].tolist()

    return [
        age,
        is_pediatric,
        is_geriatric,
        heart_rate,
        sys_bp,
        dia_bp,
        respiratory_rate,
        temperature,
        spo2,
        gcs,
        pain_scale,
        history_available,
        num_medical_conditions,
        num_observed_signs,
        arrival_mode_encoded,
        missing_vitals
    ] + embeddings
