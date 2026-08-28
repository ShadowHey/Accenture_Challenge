from typing import List
from backend.models import PatientInput

def calculate_uncertainty(missing_fields: List[str], reasons: List[str], patient: PatientInput) -> tuple:
    """
    Enhanced uncertainty calculation considering missing data, age factors,
    ambiguous symptoms, and arrival mode mismatches.
    Returns (confidence_score, uncertainty_level, escalation_flag)
    """
    confidence = 1.0

    # Each missing core vital sign reduces confidence
    core_vitals = ['heart_rate', 'spo2', 'temperature', 'respiratory_rate', 'blood_pressure']
    for v in core_vitals:
        if v in missing_fields:
            confidence -= 0.08

    # Missing medical history is a significant uncertainty factor
    if 'medical_history' in missing_fields:
        confidence -= 0.15

    # Missing GCS and pain scale add smaller uncertainty
    if 'gcs' in missing_fields:
        confidence -= 0.05
    if 'pain_scale' in missing_fields:
        confidence -= 0.03

    # Age adjustment — pediatric and geriatric patients are inherently harder to assess
    if patient.age < 18 or patient.age > 65:
        confidence -= 0.05

    # Ambiguous symptom keywords in complaint or reasons reduce confidence
    ambiguous_keywords = ['dizziness', 'vague', 'weakness', 'confusion', 'unwell', 'tired']
    combined_text = ((patient.chief_complaint or "") + " " + " ".join(reasons)).lower()
    if any(kw in combined_text for kw in ambiguous_keywords):
        confidence -= 0.1

    # Arrival mode mismatch — arrived by ambulance but presentation seems minor
    arrival = (patient.arrival_mode or "").lower()
    if arrival in ['ambulance', 'helicopter']:
        is_high_severity = any(
            'critical' in r.lower() or 'severe' in r.lower() or 'elevated' in r.lower()
            for r in reasons
        )
        if not is_high_severity:
            confidence -= 0.1

    confidence = max(0.0, round(confidence, 2))

    # Determine uncertainty level
    if confidence >= 0.8:
        uncertainty_level = 'LOW'
    elif confidence >= 0.5:
        uncertainty_level = 'MODERATE'
    else:
        uncertainty_level = 'HIGH'

    # Determine if escalation is warranted
    escalation = False
    if uncertainty_level == 'HIGH':
        escalation = True
    elif uncertainty_level == 'MODERATE' and 'medical_history' in missing_fields:
        escalation = True
    elif patient.vitals.gcs is not None and patient.vitals.gcs < 12:
        escalation = True

    return (confidence, uncertainty_level, escalation)
