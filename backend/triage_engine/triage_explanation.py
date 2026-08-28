from backend.models import PatientInput, TriageResult
from backend.triage_engine.patient_validator import validate_patient_data
from backend.triage_engine.triage_rules import evaluate_priority
from backend.triage_engine.uncertainty_calculator import calculate_uncertainty

def perform_triage(patient: PatientInput) -> TriageResult:
    """
    Orchestrates the triage logic and generates a final result.
    Stage 2: populates rules_priority and age_group.
    ML fields are populated later by the API layer after ML prediction.
    """
    # Parse blood_pressure string into structured fields if missing
    if patient.vitals.systolic_bp is None and patient.vitals.blood_pressure:
        try:
            parts = patient.vitals.blood_pressure.split('/')
            patient.vitals.systolic_bp = int(parts[0].strip())
            patient.vitals.diastolic_bp = int(parts[1].strip())
        except (ValueError, IndexError, AttributeError):
            pass

    # Step 1: Validate patient data, identify missing fields
    missing_fields = validate_patient_data(patient)

    # Step 2: Evaluate priority using age-stratified rules
    priority, reasons, age_group = evaluate_priority(patient)

    # Step 3: Calculate uncertainty and determine escalation need
    confidence, uncertainty_level, escalation = calculate_uncertainty(
        missing_fields, reasons, patient
    )

    # Store the rules-only priority before any escalation
    rules_priority = priority

    # Step 4: Apply escalation if warranted
    if escalation and priority != "LEVEL 1":
        level_num = int(priority.split(" ")[1])
        if level_num > 1:
            priority = f"LEVEL {level_num - 1}"
            reasons.append(
                f"Safety escalation: Priority upgraded from {rules_priority} to {priority} "
                f"due to {'high uncertainty' if uncertainty_level == 'HIGH' else 'missing critical data'}."
            )

    return TriageResult(
        patient_id=patient.id,
        priority=priority,
        confidence=confidence,
        uncertainty=uncertainty_level,
        escalation=escalation,
        reasons=reasons,
        missing_fields=missing_fields,
        rules_priority=rules_priority,
        age_group=age_group,
        # ML fields left as defaults — populated by API layer after ML prediction
    )
