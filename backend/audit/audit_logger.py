import time
from typing import List, Optional
from pydantic import BaseModel

class AuditEvent(BaseModel):
    """A single audit trail event. Covers all event types."""
    event_type: str        # TRIAGE, RETRIAGE, OVERRIDE, DISAGREEMENT, DETERIORATION, SURGE, DISCHARGE
    patient_id: str
    timestamp: float
    details: dict          # Flexible details per event type
    clinician_id: str = "SYSTEM"  # Simulated — default is system

class AuditLogger:
    def __init__(self):
        self.logs: List[AuditEvent] = []

    def log_event(self, event_type: str, patient_id: str, details: dict, clinician_id: str = "SYSTEM"):
        """Log any audit event."""
        event = AuditEvent(
            event_type=event_type,
            patient_id=patient_id,
            timestamp=time.time(),
            details=details,
            clinician_id=clinician_id
        )
        self.logs.append(event)

    def log_triage(self, patient_id: str, priority: str, confidence: float,
                   source: str, rules_priority: str, ml_priority: str = None):
        """Log an initial triage decision."""
        self.log_event("TRIAGE", patient_id, {
            "priority": priority,
            "confidence": confidence,
            "source": source,
            "rules_priority": rules_priority,
            "ml_priority": ml_priority
        })

    def log_retriage(self, patient_id: str, old_priority: str, new_priority: str,
                     trigger: str, confidence: float):
        """Log a re-triage event (from reassessment or deterioration)."""
        self.log_event("RETRIAGE", patient_id, {
            "old_priority": old_priority,
            "new_priority": new_priority,
            "trigger": trigger,
            "confidence": confidence
        })

    def log_override(self, patient_id: str, old_prio: str, new_prio: str,
                     reason: str, clinician_id: str = "CLINICIAN_01"):
        """Log a clinician override."""
        self.log_event("OVERRIDE", patient_id, {
            "original_priority": old_prio,
            "new_priority": new_prio,
            "reason": reason
        }, clinician_id=clinician_id)

    def log_disagreement(self, patient_id: str, rules_priority: str,
                         ml_priority: str, final_priority: str, source: str):
        """Log when rules and ML disagree."""
        self.log_event("DISAGREEMENT", patient_id, {
            "rules_priority": rules_priority,
            "ml_priority": ml_priority,
            "final_priority": final_priority,
            "resolution": source
        })

    def log_deterioration(self, patient_id: str, changed_vitals: list):
        """Log a deterioration event."""
        self.log_event("DETERIORATION", patient_id, {
            "changed_vitals": changed_vitals
        })

    def log_surge(self, action: str, patient_count: int):
        """Log surge start/stop."""
        self.log_event("SURGE", "SYSTEM", {
            "action": action,
            "patient_count": patient_count
        })

    def log_discharge(self, patient_id: str, reason: str = "discharged"):
        """Log patient discharge from queue."""
        self.log_event("DISCHARGE", patient_id, {
            "reason": reason
        })

    def get_logs(self, event_type: str = None) -> List[AuditEvent]:
        """Get logs, optionally filtered by event type. Newest first."""
        logs = self.logs
        if event_type:
            logs = [l for l in logs if l.event_type == event_type]
        return sorted(logs, key=lambda x: x.timestamp, reverse=True)

    def get_stats(self) -> dict:
        """Audit statistics for dashboard."""
        type_counts = {}
        for log in self.logs:
            type_counts[log.event_type] = type_counts.get(log.event_type, 0) + 1

        # Count ML agreement vs disagreement
        agreements = sum(1 for l in self.logs
                         if l.event_type == "TRIAGE" and l.details.get("source") == "HYBRID_AGREE")
        total_ml = sum(1 for l in self.logs
                       if l.event_type == "TRIAGE" and l.details.get("ml_priority") is not None)

        return {
            "total_events": len(self.logs),
            "event_type_counts": type_counts,
            "ml_agreement_rate": round(agreements / total_ml, 2) if total_ml > 0 else None,
            "total_overrides": type_counts.get("OVERRIDE", 0)
        }

audit_logger = AuditLogger()
