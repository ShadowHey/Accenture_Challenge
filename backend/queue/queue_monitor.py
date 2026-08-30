import time
import uuid
import os
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.models import PatientInput, TriageResult, Vitals
from backend.simulation.surge_simulator import get_normal_thresholds, get_surge_thresholds
from backend.config.profile_manager import profile_manager
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

class QueueItem(BaseModel):
    patient: PatientInput
    triage_result: TriageResult
    added_at: float
    queue_order: Optional[float] = None
    reassessment_required: bool = False
    escalation_required: bool = False
    reassessment_count: int = 0
    last_reassessed_at: Optional[float] = None
    initial_vitals: Optional[dict] = None
    completed_at: Optional[float] = None
    archived: bool = False
    wait_status: str = "WITHIN_SLA"

class QueueMonitor:
    def __init__(self):
        self.surge_mode: bool = False
        self.wait_thresholds: dict = get_normal_thresholds()
        self.active_session_id = None
        self.supabase: Optional[Client] = None
        
        if SUPABASE_URL and SUPABASE_KEY:
            try:
                self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                print(f"Error initializing Supabase client: {e}")

    def set_session(self, session_id: str):
        self.active_session_id = session_id

    def add_patient(self, patient: PatientInput, result: TriageResult, hospital_code='H001'):
        if not self.supabase or not self.active_session_id:
            return
            
        initial_v = patient.vitals.model_dump() if hasattr(patient.vitals, 'model_dump') else patient.vitals.dict()
        now = time.time()
        
        data = {
            "id": patient.id,
            "session_id": self.active_session_id,
            "hospital_code": hospital_code,
            "name": patient.name,
            "priority": result.priority,
            "vitals": initial_v,
            "triage_result": result.model_dump() if hasattr(result, 'model_dump') else result.dict(),
            "added_at": now,
            "queue_order": now,
            "reassessment_count": 0,
            "wait_status": "WITHIN_SLA",
            "archived": False,
        }
        
        # we also need patient details stored somewhere so we can reconstruct PatientInput
        # we'll store the full patient payload in a new column or merge it into vitals/triage
        # wait, the schema we created earlier doesn't have a `patient_data` column. Let me add it.
        # Ah, we'll just parse it from vitals + name, but patient input has chief complaint etc.
        # I'll just dynamically update the supabase table schema to include patient_data jsonb.
        data["patient_data"] = patient.model_dump() if hasattr(patient, 'model_dump') else patient.dict()
        
        try:
            self.supabase.table('patients').insert(data).execute()
        except Exception as e:
            print(f"DB Insert Error: {e}")

    def _row_to_queue_item(self, row: dict) -> QueueItem:
        p_data = row.get('patient_data', {})
        # Safety fallback if patient_data isn't there
        if not p_data:
            p_data = {
                "id": row.get('id', 'Unknown'),
                "name": row.get('name', 'Unknown'),
                "age": 0,
                "gender": "Unknown",
                "chief_complaint": "Unknown",
                "vitals": row.get('vitals', {}),
                "history_available": False
            }
        
        patient = PatientInput(**p_data)
        
        tr_data = row.get('triage_result', {})
        triage_result = TriageResult(**tr_data)
        
        # Ensure priority is up to date with DB if it was overridden
        triage_result.priority = row.get('priority', triage_result.priority)

        return QueueItem(
            patient=patient,
            triage_result=triage_result,
            added_at=row.get('added_at', 0),
            queue_order=row.get('queue_order', row.get('added_at', 0)),
            reassessment_required=row.get('reassessment_required', False),
            escalation_required=row.get('escalation_required', False),
            reassessment_count=row.get('reassessment_count', 0),
            wait_status=row.get('wait_status', 'WITHIN_SLA'),
            completed_at=row.get('completed_at'),
            archived=row.get('archived', False)
        )

    def get_queue(self, hospital_code=None) -> List[QueueItem]:
        if not self.supabase or not self.active_session_id:
            return []
            
        try:
            query = self.supabase.table('patients').select('*').eq('session_id', self.active_session_id).eq('archived', False).is_('completed_at', 'null')
            if hospital_code:
                query = query.eq('hospital_code', hospital_code)
            res = query.order('queue_order').execute()
            items = [self._row_to_queue_item(row) for row in res.data]
            
            # Re-evaluate reassessments on the fly
            changed_items = self._check_reassessments(items)
            
            # Batch update DB for changed items
            for row_id, updates in changed_items.items():
                self.supabase.table('patients').update(updates).eq('id', row_id).eq('session_id', self.active_session_id).execute()
                
            return sorted(items, key=lambda x: (x.triage_result.priority, x.queue_order if x.queue_order is not None else x.added_at))
        except Exception as e:
            print(f"DB Select Error: {e}")
            return []

    def get_completed_queue(self, hospital_code=None) -> List[QueueItem]:
        if not self.supabase or not self.active_session_id:
            return []
        try:
            query = self.supabase.table('patients').select('*').eq('session_id', self.active_session_id).eq('archived', False).not_.is_('completed_at', 'null')
            if hospital_code:
                query = query.eq('hospital_code', hospital_code)
            res = query.order('completed_at', desc=True).execute()
            return [self._row_to_queue_item(row) for row in res.data]
        except Exception as e:
            print(f"DB Select Completed Error: {e}")
            return []

    def archive_patient(self, patient_id: str):
        if not self.supabase or not self.active_session_id: return
        self.supabase.table('patients').update({'archived': True}).eq('id', patient_id).eq('session_id', self.active_session_id).execute()

    def _check_reassessments(self, items: List[QueueItem]) -> Dict[str, dict]:
        """Check all patients against severity-based wait thresholds and return necessary DB updates."""
        current_time = time.time()
        changed = {}
        
        for item in items:
            wait_time = current_time - item.added_at
            priority = item.triage_result.priority
            threshold = self.wait_thresholds.get(priority, 7200)
            
            orig_status = item.wait_status
            orig_req = item.reassessment_required
            
            if threshold > 0:
                if wait_time >= (threshold * 2.5):
                    item.wait_status = "SIGNIFICANTLY_OVERDUE"
                    item.reassessment_required = True
                elif wait_time >= (threshold * 1.75):
                    item.wait_status = "OVERDUE"
                    item.reassessment_required = True
                elif wait_time >= threshold:
                    item.wait_status = "REASSESSMENT_REQUIRED"
                    item.reassessment_required = True
                else:
                    item.wait_status = "WITHIN_SLA"
                    # Keep previous required state if manually escalated
            
            if item.wait_status != orig_status or item.reassessment_required != orig_req:
                changed[item.patient.id] = {
                    "wait_status": item.wait_status,
                    "reassessment_required": item.reassessment_required
                }
                
        return changed

    def update_vitals(self, patient_id: str, new_hr: Optional[int] = None,
                      new_spo2: Optional[int] = None, new_temp: Optional[float] = None,
                      new_rr: Optional[int] = None, new_gcs: Optional[int] = None,
                      new_bp: Optional[str] = None):
        """Update patient vitals and detect worsening."""
        if not self.supabase or not self.active_session_id: return
        
        # Fetch current
        res = self.supabase.table('patients').select('*').eq('id', patient_id).eq('session_id', self.active_session_id).execute()
        if not res.data: return
        
        row = res.data[0]
        item = self._row_to_queue_item(row)
        
        worsening = False
        vitals = item.patient.vitals

        if new_hr is not None:
            if vitals.heart_rate is not None and new_hr > vitals.heart_rate + 20:
                worsening = True
            elif new_hr > 120:
                worsening = True
            vitals.heart_rate = new_hr
            
        if new_bp is not None:
            vitals.blood_pressure = new_bp

        if new_spo2 is not None:
            if vitals.spo2 is not None and new_spo2 < vitals.spo2 - 3:
                worsening = True
            elif new_spo2 < 94:
                worsening = True
            vitals.spo2 = new_spo2

        if new_temp is not None:
            if vitals.temperature is not None and new_temp > vitals.temperature + 0.5:
                worsening = True
            vitals.temperature = new_temp

        if new_rr is not None:
            if vitals.respiratory_rate is not None and new_rr > vitals.respiratory_rate + 5:
                worsening = True
            vitals.respiratory_rate = new_rr

        if new_gcs is not None:
            if vitals.gcs is not None and new_gcs < vitals.gcs:
                worsening = True
            vitals.gcs = new_gcs
            
        if worsening:
            item.escalation_required = True
            item.reassessment_required = True

        updates = {
            "patient_data": item.patient.model_dump() if hasattr(item.patient, 'model_dump') else item.patient.dict(),
            "vitals": vitals.model_dump() if hasattr(vitals, 'model_dump') else vitals.dict(),
            "escalation_required": item.escalation_required,
            "reassessment_required": item.reassessment_required
        }
        self.supabase.table('patients').update(updates).eq('id', patient_id).eq('session_id', self.active_session_id).execute()

    def retriage_patient(self, patient_id: str, new_result: TriageResult, new_patient_data: Optional[PatientInput] = None):
        if not self.supabase or not self.active_session_id: return
        
        res = self.supabase.table('patients').select('reassessment_count').eq('id', patient_id).eq('session_id', self.active_session_id).execute()
        if not res.data: return
        current_count = res.data[0].get('reassessment_count', 0)
        
        updates = {
            "triage_result": new_result.model_dump() if hasattr(new_result, 'model_dump') else new_result.dict(),
            "priority": new_result.priority,
            "reassessment_required": False,
            "escalation_required": False,
            "reassessment_count": current_count + 1
        }
        if new_patient_data:
            updates["patient_data"] = new_patient_data.model_dump() if hasattr(new_patient_data, 'model_dump') else new_patient_data.dict()

        self.supabase.table('patients').update(updates).eq('id', patient_id).eq('session_id', self.active_session_id).execute()

    def activate_surge(self):
        self.surge_mode = True
        self.wait_thresholds = get_surge_thresholds()

    def deactivate_surge(self):
        self.surge_mode = False
        self.wait_thresholds = get_normal_thresholds()

    def remove_patient(self, patient_id: str):
        if not self.supabase or not self.active_session_id: return
        self.supabase.table('patients').update({'completed_at': time.time()}).eq('id', patient_id).eq('session_id', self.active_session_id).execute()

    def get_stats(self) -> dict:
        if not self.supabase or not self.active_session_id: return {}
        
        try:
            # For stats, fetch all uncompleted unarchived patients
            res = self.supabase.table('patients').select('priority, added_at, reassessment_required, escalation_required').eq('session_id', self.active_session_id).eq('archived', False).is_('completed_at', 'null').execute()
            rows = res.data
            
            current_time = time.time()
            total = len(rows)
            level_counts = {"LEVEL 1": 0, "LEVEL 2": 0, "LEVEL 3": 0, "LEVEL 4": 0, "LEVEL 5": 0}
            total_wait = 0
            reassessment_due = 0
            escalation_due = 0

            for row in rows:
                priority = row.get('priority')
                if priority in level_counts:
                    level_counts[priority] += 1
                total_wait += (current_time - row.get('added_at', current_time))
                if row.get('reassessment_required'): reassessment_due += 1
                if row.get('escalation_required'): escalation_due += 1

            avg_wait = total_wait / total if total > 0 else 0

            return {
                "total_patients": total,
                "level_counts": level_counts,
                "avg_wait_seconds": round(avg_wait, 1),
                "reassessment_due": reassessment_due,
                "escalation_due": escalation_due,
                "surge_mode": self.surge_mode,
                "active_profile_name": profile_manager.get_active_profile().get("name", "Standard General")
            }
        except Exception:
            return {}


    def override_patient(self, patient_id: str, new_priority: str, reason: str, place_before_id: Optional[str] = None, place_after_id: Optional[str] = None):
        if not self.supabase or not self.active_session_id: return None
        
        res = self.supabase.table('patients').select('*').eq('id', patient_id).eq('session_id', self.active_session_id).execute()
        if not res.data: raise Exception("Patient not found")
        
        row = res.data[0]
        item = self._row_to_queue_item(row)
        old_prio = item.triage_result.priority
        
        item.triage_result.priority = new_priority
        item.triage_result.reasons.append(f"Clinician Override: {reason}")
        item.triage_result.source = "CLINICIAN_OVERRIDE"
        
        if place_before_id or place_after_id:
            before_order, after_order = None, None
            if place_before_id:
                b_res = self.supabase.table('patients').select('queue_order').eq('id', place_before_id).eq('session_id', self.active_session_id).execute()
                if b_res.data: before_order = b_res.data[0].get('queue_order')
            if place_after_id:
                a_res = self.supabase.table('patients').select('queue_order').eq('id', place_after_id).eq('session_id', self.active_session_id).execute()
                if a_res.data: after_order = a_res.data[0].get('queue_order')
                
            if before_order is not None and after_order is not None:
                item.queue_order = (before_order + after_order) / 2.0
            elif before_order is not None:
                item.queue_order = before_order - 1.0
            elif after_order is not None:
                item.queue_order = after_order + 1.0
        else:
            if old_prio != new_priority:
                item.queue_order = time.time()
                
        updates = {
            "priority": new_priority,
            "triage_result": item.triage_result.model_dump() if hasattr(item.triage_result, 'model_dump') else item.triage_result.dict(),
            "queue_order": item.queue_order
        }
        self.supabase.table('patients').update(updates).eq('id', patient_id).eq('session_id', self.active_session_id).execute()
        return old_prio

    def get_patient(self, patient_id: str, hospital_code: str = None) -> Optional[QueueItem]:
        if not self.supabase or not self.active_session_id: return None
        query = self.supabase.table('patients').select('*').eq('id', patient_id).eq('session_id', self.active_session_id)
        if hospital_code:
            query = query.eq('hospital_code', hospital_code)
        res = query.execute()
        if not res.data: return None
        return self._row_to_queue_item(res.data[0])

    def has_patient(self, patient_id: str, hospital_code: str = None) -> bool:
        return self.get_patient(patient_id, hospital_code=hospital_code) is not None
        
    def clear_all(self, hospital_code=None):
        if not self.supabase or not self.active_session_id: return
        query = self.supabase.table('patients').delete().eq('session_id', self.active_session_id)
        if hospital_code:
            query = query.eq('hospital_code', hospital_code)
        query.execute()

queue_manager = QueueMonitor()
