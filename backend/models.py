from pydantic import BaseModel
from typing import List, Optional

class Vitals(BaseModel):
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    spo2: Optional[int] = None
    gcs: Optional[int] = None            # Glasgow Coma Scale (3-15)
    pain_scale: Optional[int] = None     # 0-10

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
    arrival_mode: Optional[str] = None   # walk-in, ambulance, helicopter
    symptoms: Optional[List[str]] = []   # structured symptom list

class TriageResult(BaseModel):
    patient_id: str
    priority: str                          # LEVEL 1-5 (final)
    confidence: float                      # 0.0-1.0
    uncertainty: str                       # LOW / MODERATE / HIGH
    escalation: bool
    reasons: List[str]
    missing_fields: List[str]
    rules_priority: str = ""               # what rules engine assigned
    ml_priority: Optional[str] = None      # what ML assigned (None if ML unavailable)
    ml_confidence: Optional[float] = None  # ML model confidence
    age_group: str = "ADULT"               # PEDIATRIC / ADULT / GERIATRIC
    source: str = "RULES"                  # RULES / ML_ESCALATED / HYBRID_AGREE / RULES_FLOOR
    disagreement: Optional[str] = None     # explanation if rules and ML disagree
    feature_importances: Optional[dict] = None  # top ML feature importances
