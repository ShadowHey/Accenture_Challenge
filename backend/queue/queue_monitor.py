import time
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.models import PatientInput, TriageResult
from backend.simulation.surge_simulator import get_normal_thresholds, get_surge_thresholds

class QueueItem(BaseModel):
    patient: PatientInput
    triage_result: TriageResult
    added_at: float
    reassessment_required: bool = False
    escalation_required: bool = False
    reassessment_count: int = 0        # how many times this patient has been re-assessed
    last_reassessed_at: Optional[float] = None

class QueueMonitor:
    def __init__(self):
        self.queue: Dict[str, QueueItem] = {}
        self.surge_mode: bool = False
        self.wait_thresholds: dict = get_normal_thresholds()

    def add_patient(self, patient: PatientInput, result: TriageResult):
        self.queue[patient.id] = QueueItem(
            patient=patient,
            triage_result=result,
            added_at=time.time()
        )

    def get_queue(self) -> List[QueueItem]:
        self._check_reassessments()
        # Return sorted by priority (LEVEL 1 first) then by wait time (longest first)
        return sorted(
            self.queue.values(),
            key=lambda x: (x.triage_result.priority, x.added_at)
        )

    def _check_reassessments(self):
        """Check all patients against severity-based wait thresholds."""
        current_time = time.time()
        for item in self.queue.values():
            wait_time = current_time - item.added_at
            priority = item.triage_result.priority
            threshold = self.wait_thresholds.get(priority, 7200)
            if threshold > 0 and wait_time > threshold:
                item.reassessment_required = True

    def update_vitals(self, patient_id: str, new_hr: Optional[int] = None,
                      new_spo2: Optional[int] = None, new_temp: Optional[float] = None,
                      new_rr: Optional[int] = None, new_gcs: Optional[int] = None):
        """Update patient vitals and detect worsening."""
        if patient_id not in self.queue:
            return

        item = self.queue[patient_id]
        worsening = False

        if new_hr is not None:
            old_hr = item.patient.vitals.heart_rate
            if old_hr is not None and new_hr > old_hr + 20:
                worsening = True
            elif new_hr > 120:
                worsening = True
            item.patient.vitals.heart_rate = new_hr

        if new_spo2 is not None:
            old_spo2 = item.patient.vitals.spo2
            if old_spo2 is not None and new_spo2 < old_spo2 - 3:
                worsening = True
            elif new_spo2 < 94:
                worsening = True
            item.patient.vitals.spo2 = new_spo2

        if new_temp is not None:
            old_temp = item.patient.vitals.temperature
            if old_temp is not None and new_temp > old_temp + 0.5:
                worsening = True
            item.patient.vitals.temperature = new_temp

        if new_rr is not None:
            old_rr = item.patient.vitals.respiratory_rate
            if old_rr is not None and new_rr > old_rr + 5:
                worsening = True
            item.patient.vitals.respiratory_rate = new_rr

        if new_gcs is not None:
            old_gcs = item.patient.vitals.gcs
            if old_gcs is not None and new_gcs < old_gcs:
                worsening = True
            item.patient.vitals.gcs = new_gcs

        if worsening:
            item.escalation_required = True
            item.reassessment_required = True

    def retriage_patient(self, patient_id: str, new_result: TriageResult):
        """Apply a new triage result after re-assessment."""
        if patient_id in self.queue:
            item = self.queue[patient_id]
            item.triage_result = new_result
            item.reassessment_required = False
            item.escalation_required = False
            item.reassessment_count += 1
            item.last_reassessed_at = time.time()

    def activate_surge(self):
        """Activate surge mode — halve all wait thresholds."""
        self.surge_mode = True
        self.wait_thresholds = get_surge_thresholds()

    def deactivate_surge(self):
        """Deactivate surge mode — restore normal thresholds."""
        self.surge_mode = False
        self.wait_thresholds = get_normal_thresholds()

    def remove_patient(self, patient_id: str):
        if patient_id in self.queue:
            del self.queue[patient_id]

    def get_stats(self) -> dict:
        """Return queue statistics for the dashboard."""
        current_time = time.time()
        total = len(self.queue)
        level_counts = {"LEVEL 1": 0, "LEVEL 2": 0, "LEVEL 3": 0, "LEVEL 4": 0, "LEVEL 5": 0}
        total_wait = 0
        reassessment_due = 0
        escalation_due = 0

        for item in self.queue.values():
            priority = item.triage_result.priority
            if priority in level_counts:
                level_counts[priority] += 1
            total_wait += (current_time - item.added_at)
            if item.reassessment_required:
                reassessment_due += 1
            if item.escalation_required:
                escalation_due += 1

        avg_wait = total_wait / total if total > 0 else 0

        return {
            "total_patients": total,
            "level_counts": level_counts,
            "avg_wait_seconds": round(avg_wait, 1),
            "reassessment_due": reassessment_due,
            "escalation_due": escalation_due,
            "surge_mode": self.surge_mode
        }

queue_manager = QueueMonitor()
