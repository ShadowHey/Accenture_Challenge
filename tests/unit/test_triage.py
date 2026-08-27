import pytest
from backend.models import PatientInput, Vitals
from backend.triage_engine.triage_rules import evaluate_priority
from backend.triage_engine.uncertainty_calculator import calculate_uncertainty

def test_evaluate_priority_level_1():
    patient = PatientInput(
        id="T1", name="Test1", age=50, gender="M", chief_complaint="Chest pain",
        vitals=Vitals(heart_rate=160, blood_pressure="120/80", respiratory_rate=20, temperature=37.0, spo2=95),
        history_available=False, medical_history=[], observed_signs=[]
    )
    priority, reasons = evaluate_priority(patient)
    assert priority == "LEVEL 1"

def test_evaluate_priority_level_2():
    patient = PatientInput(
        id="T2", name="Test2", age=70, gender="M", chief_complaint="Severe chest pain",
        vitals=Vitals(heart_rate=90, blood_pressure="120/80", respiratory_rate=20, temperature=37.0, spo2=98),
        history_available=False, medical_history=[], observed_signs=[]
    )
    priority, reasons = evaluate_priority(patient)
    assert priority == "LEVEL 2"
    assert any("Geriatric patient with chest pain" in r for r in reasons)

def test_uncertainty_calculator():
    # Test high confidence
    conf, level, esc = calculate_uncertainty([], ["Clear symptom"])
    assert conf == 1.0
    assert level == "LOW"
    assert esc == False

    # Test missing history and vitals
    conf, level, esc = calculate_uncertainty(["medical_history", "heart_rate"], ["Vague symptom"])
    # 1.0 - 0.15 (hist) - 0.1 (hr) - 0.1 (ambiguous) = 0.65 (MODERATE)
    assert conf == 0.65
    assert level == "MODERATE"
    # Escalate because moderate uncertainty + missing history
    assert esc == True
