import re
from backend.models import PatientInput

FEATURE_NAMES = [
    "age",
    "is_pediatric",
    "is_geriatric",
    "heart_rate",
    "systolic_bp",
    "diastolic_bp",
    "respiratory_rate",
    "temperature",
    "spo2",
    "gcs",
    "pain_scale",
    "history_available",
    "num_medical_conditions",
    "num_observed_signs",
    "arrival_mode_encoded",
    "complaint_severity_score",
    "num_missing_vitals",
    "is_chest_pain",
    "is_respiratory",
    "is_trauma",
    "is_neurological",
    "is_abdominal"
]

def _parse_bp(patient: PatientInput):
    """Extract systolic/diastolic BP from structured fields or string."""
    sys_val = patient.vitals.systolic_bp
    dia_val = patient.vitals.diastolic_bp
    if (sys_val is None or dia_val is None) and patient.vitals.blood_pressure:
        match = re.match(r"(\d+)/(\d+)", patient.vitals.blood_pressure)
        if match:
            if sys_val is None: sys_val = int(match.group(1))
            if dia_val is None: dia_val = int(match.group(2))
    return sys_val or 0, dia_val or 0

def extract_features(patient: PatientInput) -> list:
    """
    Extracts a 22-feature numeric vector from a PatientInput object.
    Missing vitals are encoded as 0. num_missing_vitals captures missingness as a signal.
    """
    age = patient.age
    is_pediatric = 1 if age < 18 else 0
    is_geriatric = 1 if age > 65 else 0

    # Vitals — access through patient.vitals
    heart_rate = patient.vitals.heart_rate or 0
    sys_bp, dia_bp = _parse_bp(patient)
    respiratory_rate = patient.vitals.respiratory_rate or 0
    temperature = float(patient.vitals.temperature) if patient.vitals.temperature else 0.0
    spo2 = patient.vitals.spo2 or 0
    gcs = patient.vitals.gcs or 0
    pain_scale = patient.vitals.pain_scale or 0

    # History and observed signs
    history_available = 1 if patient.history_available else 0
    num_medical_conditions = len(patient.medical_history) if patient.medical_history else 0
    num_observed_signs = len(patient.observed_signs) if patient.observed_signs else 0

    # Arrival mode encoding: 0=walk-in/unknown, 1=ambulance, 2=helicopter
    arrival_mode = (patient.arrival_mode or "").lower()
    if arrival_mode == "ambulance":
        arrival_mode_encoded = 1
    elif arrival_mode == "helicopter":
        arrival_mode_encoded = 2
    else:
        arrival_mode_encoded = 0

    # Chief complaint severity score (0-3 based on keywords)
    complaint = (patient.chief_complaint or "").lower()

    if any(k in complaint for k in ["cardiac arrest", "unresponsive", "stroke", "stemi", "gunshot"]):
        complaint_severity_score = 3
    elif any(k in complaint for k in ["chest pain", "shortness of breath", "severe", "fracture", "unconscious"]):
        complaint_severity_score = 2
    elif any(k in complaint for k in ["fever", "cough", "nausea", "dizziness", "pain", "vomiting"]):
        complaint_severity_score = 1
    else:
        complaint_severity_score = 0

    # Count missing vitals
    missing_vitals = 0
    if patient.vitals.heart_rate is None: missing_vitals += 1
    if patient.vitals.blood_pressure is None and patient.vitals.systolic_bp is None: missing_vitals += 1
    if patient.vitals.respiratory_rate is None: missing_vitals += 1
    if patient.vitals.temperature is None: missing_vitals += 1
    if patient.vitals.spo2 is None: missing_vitals += 1

    # Binary chief complaint category flags
    is_chest_pain = 1 if "chest pain" in complaint else 0
    is_respiratory = 1 if any(k in complaint for k in ["breath", "respiratory", "cough", "wheez", "asthma"]) else 0
    is_trauma = 1 if any(k in complaint for k in ["trauma", "fall", "accident", "laceration", "wound", "fracture", "bleed", "mva"]) else 0
    is_neurological = 1 if any(k in complaint for k in ["stroke", "seizure", "unresponsive", "dizz", "headache", "confus"]) else 0
    is_abdominal = 1 if any(k in complaint for k in ["abdomin", "stomach", "nausea", "vomit"]) else 0

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
        complaint_severity_score,
        missing_vitals,
        is_chest_pain,
        is_respiratory,
        is_trauma,
        is_neurological,
        is_abdominal
    ]
