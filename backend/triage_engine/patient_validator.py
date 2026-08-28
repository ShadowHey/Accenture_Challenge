from backend.models import PatientInput

def validate_patient_data(patient: PatientInput) -> list:
    """
    Validates patient data and returns a list of missing or problematic fields.
    Checks all vital fields including new Stage 2 fields.
    """
    missing_fields = []

    # Check core vital signs
    if patient.vitals.heart_rate is None:
        missing_fields.append("heart_rate")
    if patient.vitals.respiratory_rate is None:
        missing_fields.append("respiratory_rate")
    if patient.vitals.temperature is None:
        missing_fields.append("temperature")
    if patient.vitals.spo2 is None:
        missing_fields.append("spo2")

    # Check blood pressure — either structured or parseable string
    has_structured_bp = (patient.vitals.systolic_bp is not None and
                         patient.vitals.diastolic_bp is not None)
    if not has_structured_bp:
        bp_str = patient.vitals.blood_pressure
        can_parse_bp = False
        if bp_str:
            try:
                parts = bp_str.split('/')
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    can_parse_bp = True
            except (AttributeError, ValueError):
                pass
        if not can_parse_bp:
            missing_fields.append("blood_pressure")

    # Check GCS and pain_scale (new in Stage 2)
    if patient.vitals.gcs is None:
        missing_fields.append("gcs")
    if patient.vitals.pain_scale is None:
        missing_fields.append("pain_scale")

    # Check medical history availability
    if not patient.history_available:
        missing_fields.append("medical_history")

    return missing_fields
