from backend.models import PatientInput

def validate_patient_data(patient: PatientInput):
    """
    Validates patient data and returns a list of missing or problematic fields.
    """
    missing_fields = []
    
    if patient.vitals.heart_rate is None:
        missing_fields.append("heart_rate")
    if patient.vitals.blood_pressure is None:
        missing_fields.append("blood_pressure")
    if patient.vitals.respiratory_rate is None:
        missing_fields.append("respiratory_rate")
    if patient.vitals.temperature is None:
        missing_fields.append("temperature")
    if patient.vitals.spo2 is None:
        missing_fields.append("spo2")
        
    if not patient.history_available:
        missing_fields.append("medical_history")
        
    return missing_fields
