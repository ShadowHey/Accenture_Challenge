from backend.models import PatientInput

def evaluate_priority(patient: PatientInput):
    """
    Evaluates patient to determine priority level (LEVEL 1 to LEVEL 5)
    and collects reasons.
    """
    reasons = []
    priority = "LEVEL 5"
    
    # Extract vitals with defaults for missing
    hr = patient.vitals.heart_rate or 80
    spo2 = patient.vitals.spo2 or 98
    temp = patient.vitals.temperature or 37.0
    rr = patient.vitals.respiratory_rate or 16
    
    # Age categories
    is_pediatric = patient.age < 18
    is_geriatric = patient.age > 65

    # LEVEL 1 checks
    if hr > 150 or hr < 50 or spo2 < 90 or "Unresponsive" in patient.observed_signs or "Cyanotic" in patient.observed_signs:
        priority = "LEVEL 1"
        reasons.append("Critical vital signs (extreme HR or SpO2 < 90) or unresponsiveness observed.")
        return priority, reasons
        
    # LEVEL 2 checks
    if hr > 120 or spo2 < 94 or temp > 39.0 or "Severe" in patient.chief_complaint or "chest pain" in patient.chief_complaint.lower():
        priority = "LEVEL 2"
        if is_geriatric and "chest pain" in patient.chief_complaint.lower():
            reasons.append("Geriatric patient with chest pain is high risk.")
        else:
            reasons.append("Abnormal vitals (HR > 120 or SpO2 < 94 or Temp > 39) or concerning severe symptom.")
        return priority, reasons

    # LEVEL 3 checks
    if hr > 100 or "pain" in patient.chief_complaint.lower() or "dizziness" in patient.chief_complaint.lower():
        priority = "LEVEL 3"
        if is_pediatric and temp > 38.0:
            reasons.append("Pediatric patient with fever requires urgent attention.")
        else:
            reasons.append("Elevated heart rate or concerning symptoms requiring urgent evaluation.")
        return priority, reasons
        
    # LEVEL 4 checks
    if "sprain" in patient.chief_complaint.lower() or "minor" in patient.chief_complaint.lower():
        priority = "LEVEL 4"
        reasons.append("Minor injury or stable presentation.")
        return priority, reasons
        
    # Default LEVEL 5
    reasons.append("Vitals are stable and complaint does not indicate urgent risk.")
    return priority, reasons
