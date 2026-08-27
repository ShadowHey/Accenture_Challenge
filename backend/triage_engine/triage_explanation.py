from backend.models import PatientInput, TriageResult
from backend.triage_engine.patient_validator import validate_patient_data
from backend.triage_engine.triage_rules import evaluate_priority
from backend.triage_engine.uncertainty_calculator import calculate_uncertainty

def perform_triage(patient: PatientInput) -> TriageResult:
    """
    Orchestrates the triage logic and generates a final result.
    """
    missing_fields = validate_patient_data(patient)
    priority, reasons = evaluate_priority(patient)
    confidence, uncertainty_level, escalation = calculate_uncertainty(missing_fields, reasons)
    
    if escalation:
        reasons.append("Safety Escalation: Missing critical info for a potentially concerning presentation.")
        
        # If escalation is required, we bump the priority by 1 level if not already Level 1
        level_num = int(priority.split(" ")[1])
        if level_num > 1:
            priority = f"LEVEL {level_num - 1}"
            reasons.append(f"Priority escalated to {priority} due to high uncertainty.")

    return TriageResult(
        patient_id=patient.id,
        priority=priority,
        confidence=confidence,
        uncertainty=uncertainty_level,
        escalation=escalation,
        reasons=reasons,
        missing_fields=missing_fields
    )
