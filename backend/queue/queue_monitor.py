import time
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.models import PatientInput, TriageResult

class QueueItem(BaseModel):
    patient: PatientInput
    triage_result: TriageResult
    added_at: float
    reassessment_required: bool = False
    escalation_required: bool = False

class QueueMonitor:
    def __init__(self):
        self.queue: Dict[str, QueueItem] = {}
        # Simple configurable threshold in seconds (e.g. 60 seconds for demo)
        self.wait_threshold = 60 
        
    def add_patient(self, patient: PatientInput, result: TriageResult):
        self.queue[patient.id] = QueueItem(
            patient=patient,
            triage_result=result,
            added_at=time.time()
        )
        
    def get_queue(self) -> List[QueueItem]:
        self._check_reassessments()
        # Return sorted by priority (LEVEL 1 first) then by wait time
        return sorted(
            self.queue.values(),
            key=lambda x: (x.triage_result.priority, x.added_at)
        )
        
    def _check_reassessments(self):
        current_time = time.time()
        for item in self.queue.values():
            wait_time = current_time - item.added_at
            if wait_time > self.wait_threshold:
                item.reassessment_required = True

    def update_vitals(self, patient_id: str, new_hr: Optional[int], new_spo2: Optional[int]):
        if patient_id in self.queue:
            item = self.queue[patient_id]
            # Simple worsening check
            worsening = False
            if new_hr and new_hr > 120 and (not item.patient.vitals.heart_rate or item.patient.vitals.heart_rate <= 120):
                worsening = True
            if new_spo2 and new_spo2 < 94 and (not item.patient.vitals.spo2 or item.patient.vitals.spo2 >= 94):
                worsening = True
                
            if worsening:
                item.escalation_required = True
                item.reassessment_required = True
                
            # Update vitals
            if new_hr: item.patient.vitals.heart_rate = new_hr
            if new_spo2: item.patient.vitals.spo2 = new_spo2
            
    def remove_patient(self, patient_id: str):
        if patient_id in self.queue:
            del self.queue[patient_id]
            
queue_manager = QueueMonitor()
