import pytest
from backend.models import PatientInput, Vitals
from backend.triage_engine.triage_rules import evaluate_priority, get_age_group
from backend.ml.feature_extractor import extract_features
from backend.ml.reconciler import reconcile
from backend.queue.queue_monitor import QueueMonitor
from backend.simulation.patient_generator import generate_patient

def test_age_stratified_rules():
    # Pediatric critical HR
    p_ped = PatientInput(
        id='1', name='Ped', age=1, gender='M', chief_complaint='Fever',
        vitals=Vitals(heart_rate=190, spo2=98, temperature=37.5, respiratory_rate=30, gcs=15, pain_scale=2),
        history_available=False, medical_history=[], observed_signs=[]
    )
    priority, reasons, age_group = evaluate_priority(p_ped)
    assert age_group == 'PEDIATRIC'
    assert priority == 'LEVEL 1'
    assert any("Critical high HR" in r for r in reasons)

    # Geriatric lower temp threshold
    p_ger = PatientInput(
        id='2', name='Ger', age=80, gender='F', chief_complaint='Unwell',
        vitals=Vitals(heart_rate=80, spo2=96, temperature=38.6, respiratory_rate=18, gcs=15, pain_scale=2),
        history_available=False, medical_history=[], observed_signs=[]
    )
    priority, reasons, age_group = evaluate_priority(p_ger)
    assert age_group == 'GERIATRIC'
    assert priority == 'LEVEL 2'
    assert any("Concerning temp" in r for r in reasons)

def test_ml_feature_extraction():
    p = PatientInput(
        id='TEST1', name='Test', age=45, gender='M',
        chief_complaint='Chest pain and nausea',
        vitals=Vitals(heart_rate=110, blood_pressure='140/90', spo2=95, temperature=37.0, respiratory_rate=18, gcs=15, pain_scale=7),
        history_available=True, medical_history=['Hypertension'], observed_signs=['Alert'],
        arrival_mode='ambulance'
    )
    features = extract_features(p)
    # Check features: age(0), is_pediatric(1), is_geriatric(2), HR(3), sys_bp(4), dia_bp(5)
    # arrival_mode_encoded(14), complaint_severity_score(15), is_chest_pain(17)
    assert features[0] == 45
    assert features[1] == 0
    assert features[2] == 0
    assert features[3] == 110
    assert features[4] == 140
    assert features[5] == 90
    assert features[14] == 1  # ambulance
    assert features[15] == 0  # missing_vitals
    assert len(features) == 16 + 384  # base + embeddings

def test_reconciler_safety():
    # ML escalation allowed
    final, src, msg = reconcile('LEVEL 3', 0.8, 'LEVEL 2', 0.9)
    assert final == 'LEVEL 2'
    assert src == 'ML_ESCALATED'

    # ML downgrade denied
    final, src, msg = reconcile('LEVEL 2', 0.8, 'LEVEL 3', 0.9)
    assert final == 'LEVEL 2'
    assert src == 'RULES_FLOOR'

    # Agreement
    final, src, msg = reconcile('LEVEL 3', 0.8, 'LEVEL 3', 0.9)
    assert final == 'LEVEL 3'
    assert src == 'HYBRID_AGREE'

def test_queue_severity_thresholds():
    qm = QueueMonitor()
    assert qm.wait_thresholds['LEVEL 2'] == 600
    
    qm.activate_surge()
    assert qm.wait_thresholds['LEVEL 2'] == 300
    
    qm.deactivate_surge()
    assert qm.wait_thresholds['LEVEL 2'] == 600

def test_patient_generator():
    p = generate_patient(archetype='CARDIAC')
    assert p.age >= 35 and p.age <= 80
    assert p.id.startswith('SURGE_')
