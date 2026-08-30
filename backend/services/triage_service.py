from backend.models import PatientInput, TriageResult
from backend.triage_engine.triage_explanation import perform_triage
from backend.ml.predictor import predict_triage
from backend.ml.reconciler import reconcile
from backend.audit.audit_logger import audit_logger

import os
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
    Run the complete hybrid triage pipeline:
    1. Deterministic rules engine → rules_priority
    2. ML model → ml_priority (advisory)
    3. Reconciler → final priority (ML can escalate, never downgrade)
    4. Log everything to audit trail
    """
    # Step 1: Rules-based triage
    result = perform_triage(patient)

    # Step 2: ML prediction
    ml_priority, ml_confidence, feature_importances = predict_triage(patient)

    # Step 3: Reconcile rules + ML
    final_priority, source, disagreement = reconcile(
        result.priority, result.confidence, ml_priority, ml_confidence
    )

    # Update result with ML and reconciliation data
    result.ml_priority = ml_priority
    result.ml_confidence = ml_confidence
    result.feature_importances = feature_importances
    result.source = source
    result.disagreement = disagreement
    result.priority = final_priority

    # Step 4: Audit logging
    audit_logger.log_triage(
        patient.id, final_priority, result.confidence,
        source, result.rules_priority, ml_priority
    )

    # Log disagreement separately if it occurred
    if disagreement and source in ("ML_ESCALATED", "RULES_FLOOR"):
        audit_logger.log_disagreement(
            patient.id, result.rules_priority,
            ml_priority, final_priority, source
        )

    return result
