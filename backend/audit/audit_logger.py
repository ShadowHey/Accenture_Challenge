import time
from typing import List
from pydantic import BaseModel

class OverrideRecord(BaseModel):
    patient_id: str
    original_priority: str
    new_priority: str
    reason: str
    timestamp: float

class AuditLogger:
    def __init__(self):
        self.logs: List[OverrideRecord] = []
        
    def log_override(self, patient_id: str, old_prio: str, new_prio: str, reason: str):
        record = OverrideRecord(
            patient_id=patient_id,
            original_priority=old_prio,
            new_priority=new_prio,
            reason=reason,
            timestamp=time.time()
        )
        self.logs.append(record)
        
    def get_logs(self) -> List[OverrideRecord]:
        return sorted(self.logs, key=lambda x: x.timestamp, reverse=True)

audit_logger = AuditLogger()
