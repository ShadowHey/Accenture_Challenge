from pydantic import BaseModel
from typing import List, Optional

class Vitals(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None

class PatientInput(BaseModel):
    id: str
    name: str
    age: int
    gender: str
    chief_complaint: str
    vitals: Vitals
    history_available: bool
    medical_history: List[str] = []
    observed_signs: List[str] = []

class TriageResult(BaseModel):
    patient_id: str
    priority: str
    confidence: float
    uncertainty: str
    escalation: bool
    reasons: List[str]
    missing_fields: List[str]
