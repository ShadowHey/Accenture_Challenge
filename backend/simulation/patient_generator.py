from __future__ import annotations
import random
import numpy as np
import uuid
from backend.models import PatientInput, Vitals

ARCHETYPES = {
    'CARDIAC': {
        'name': 'Cardiac',
        'complaint_templates': ['chest pain', 'chest tightness', 'heart palpitations', 'left arm pain'],
        'symptom_templates': [['shortness of breath'], ['nausea', 'sweating'], ['dizziness']],
        'vital_ranges': {
            'heart_rate': (110, 20),
            'systolic_bp': (150, 30),
            'diastolic_bp': (90, 15),
            'respiratory_rate': (22, 4),
            'temperature': (37.0, 0.4),
            'spo2': (94, 3)
        },
        'age_range': (35, 80),
        'arrival_modes': [('ambulance', 0.8), ('walk-in', 0.2)],
        'sign_templates': [['diaphoretic', 'pale'], ['clutching chest']],
        'history_templates': [['hypertension', 'hyperlipidemia'], ['previous MI'], ['diabetes']],
        'severity_distribution': {'LEVEL 1': 0.1, 'LEVEL 2': 0.7, 'LEVEL 3': 0.2}
    },
    'RESPIRATORY': {
        'name': 'Respiratory',
        'complaint_templates': ['shortness of breath', 'difficulty breathing', 'wheezing', 'severe cough'],
        'symptom_templates': [['cough', 'fever'], ['chest tightness'], ['fatigue']],
        'vital_ranges': {
            'heart_rate': (105, 15),
            'systolic_bp': (130, 20),
            'diastolic_bp': (80, 10),
            'respiratory_rate': (26, 6),
            'temperature': (37.8, 1.0),
            'spo2': (89, 5)
        },
        'age_range': (5, 85),
        'arrival_modes': [('ambulance', 0.5), ('walk-in', 0.5)],
        'sign_templates': [['cyanosis'], ['accessory muscle use', 'wheezing'], ['tripoding']],
        'history_templates': [['COPD'], ['asthma'], ['smoker']],
        'severity_distribution': {'LEVEL 1': 0.05, 'LEVEL 2': 0.4, 'LEVEL 3': 0.4, 'LEVEL 4': 0.15}
    },
    'TRAUMA': {
        'name': 'Trauma',
        'complaint_templates': ['MVA', 'fall from height', 'stab wound', 'head injury'],
        'symptom_templates': [['pain'], ['bleeding', 'confusion'], ['loss of consciousness']],
        'vital_ranges': {
            'heart_rate': (120, 25),
            'systolic_bp': (110, 35),
            'diastolic_bp': (70, 20),
            'respiratory_rate': (24, 6),
            'temperature': (36.8, 0.5),
            'spo2': (96, 3)
        },
        'age_range': (15, 65),
        'arrival_modes': [('ambulance', 0.8), ('helicopter', 0.2)],
        'sign_templates': [['obvious deformity', 'active bleeding'], ['abrasions', 'bruising']],
        'history_templates': [[], ['no significant history']],
        'severity_distribution': {'LEVEL 1': 0.3, 'LEVEL 2': 0.5, 'LEVEL 3': 0.2}
    },
    'PEDIATRIC_FEVER': {
        'name': 'Pediatric Fever',
        'complaint_templates': ['high fever', 'fussy', 'rash', 'not eating'],
        'symptom_templates': [['crying', 'lethargic'], ['vomiting'], ['ear pulling']],
        'vital_ranges': {
            'heart_rate': (140, 20),
            'systolic_bp': (90, 15),
            'diastolic_bp': (55, 10),
            'respiratory_rate': (30, 8),
            'temperature': (39.5, 0.8),
            'spo2': (98, 2)
        },
        'age_range': (0, 12),
        'arrival_modes': [('walk-in', 0.9), ('ambulance', 0.1)],
        'sign_templates': [['flushed', 'warm to touch'], ['crying but consolable']],
        'history_templates': [[], ['recent URI']],
        'severity_distribution': {'LEVEL 2': 0.1, 'LEVEL 3': 0.5, 'LEVEL 4': 0.3, 'LEVEL 5': 0.1}
    },
    'GERIATRIC_FALL': {
        'name': 'Geriatric Fall',
        'complaint_templates': ['fall at home', 'hip pain', 'confusion after fall'],
        'symptom_templates': [['leg pain', 'unable to bear weight'], ['headache', 'dizziness']],
        'vital_ranges': {
            'heart_rate': (90, 15),
            'systolic_bp': (145, 25),
            'diastolic_bp': (85, 15),
            'respiratory_rate': (18, 4),
            'temperature': (37.0, 0.5),
            'spo2': (95, 3)
        },
        'age_range': (65, 95),
        'arrival_modes': [('ambulance', 0.7), ('walk-in', 0.3)],
        'sign_templates': [['shortened and externally rotated leg'], ['skin tear', 'hematoma']],
        'history_templates': [['osteoporosis', 'hypertension'], ['dementia'], ['atrial fibrillation']],
        'severity_distribution': {'LEVEL 2': 0.3, 'LEVEL 3': 0.6, 'LEVEL 4': 0.1}
    },
    'ABDOMINAL': {
        'name': 'Abdominal',
        'complaint_templates': ['severe abdominal pain', 'vomiting blood', 'stomach ache'],
        'symptom_templates': [['nausea', 'vomiting'], ['diarrhea', 'cramping'], ['fever', 'chills']],
        'vital_ranges': {
            'heart_rate': (100, 15),
            'systolic_bp': (120, 20),
            'diastolic_bp': (75, 15),
            'respiratory_rate': (18, 4),
            'temperature': (37.8, 0.8),
            'spo2': (98, 2)
        },
        'age_range': (18, 70),
        'arrival_modes': [('walk-in', 0.7), ('ambulance', 0.3)],
        'sign_templates': [['guarding', 'rebound tenderness'], ['pale', 'sweaty']],
        'history_templates': [['gallstones'], ['GERD'], ['previous abdominal surgery']],
        'severity_distribution': {'LEVEL 2': 0.2, 'LEVEL 3': 0.5, 'LEVEL 4': 0.3}
    },
    'NEUROLOGICAL': {
        'name': 'Neurological',
        'complaint_templates': ['worst headache of life', 'facial droop', 'seizure', 'weakness'],
        'symptom_templates': [['slurred speech', 'arm weakness'], ['vision changes'], ['numbness']],
        'vital_ranges': {
            'heart_rate': (95, 20),
            'systolic_bp': (160, 30),
            'diastolic_bp': (95, 20),
            'respiratory_rate': (16, 4),
            'temperature': (37.0, 0.5),
            'spo2': (97, 3)
        },
        'age_range': (30, 85),
        'arrival_modes': [('ambulance', 0.8), ('walk-in', 0.2)],
        'sign_templates': [['unilateral weakness'], ['aphasia', 'gaze deviation'], ['post-ictal']],
        'history_templates': [['hypertension', 'previous TIA'], ['epilepsy']],
        'severity_distribution': {'LEVEL 1': 0.2, 'LEVEL 2': 0.6, 'LEVEL 3': 0.2}
    },
    'MINOR_INJURY': {
        'name': 'Minor Injury',
        'complaint_templates': ['sprained ankle', 'cut on hand', 'sore throat', 'finger pain'],
        'symptom_templates': [['swelling'], ['bleeding stopped'], ['pain with swallowing']],
        'vital_ranges': {
            'heart_rate': (85, 10),
            'systolic_bp': (120, 15),
            'diastolic_bp': (80, 10),
            'respiratory_rate': (16, 2),
            'temperature': (37.1, 0.4),
            'spo2': (99, 1)
        },
        'age_range': (5, 60),
        'arrival_modes': [('walk-in', 1.0)],
        'sign_templates': [['mild edema', 'ecchymosis'], ['small laceration']],
        'history_templates': [[], ['otherwise healthy']],
        'severity_distribution': {'LEVEL 4': 0.6, 'LEVEL 5': 0.4}
    }
}

def generate_patient(archetype: str = None, patient_id: str = None) -> PatientInput:
    if archetype is None or archetype not in ARCHETYPES:
        archetype = random.choice(list(ARCHETYPES.keys()))
    
    arch_data = ARCHETYPES[archetype]
    
    if patient_id is None:
        patient_id = f"SURGE_{uuid.uuid4().hex[:6].upper()}"
        
    age = random.randint(arch_data['age_range'][0], arch_data['age_range'][1])
    gender = random.choice(['M', 'F'])
    
    complaint = random.choice(arch_data['complaint_templates'])
    symptoms = random.choice(arch_data['symptom_templates']) if arch_data['symptom_templates'] else []
    signs = random.choice(arch_data['sign_templates']) if arch_data['sign_templates'] else []
    history = random.choice(arch_data['history_templates']) if arch_data['history_templates'] else []
    
    modes, weights = zip(*arch_data['arrival_modes'])
    arrival_mode = random.choices(modes, weights=weights, k=1)[0]
    
    vitals_dict = {}
    for vital, (mean, std) in arch_data['vital_ranges'].items():
        if random.random() < 0.2:
            vitals_dict[vital] = None
        else:
            val = np.random.normal(mean, std)
            if vital in ['heart_rate', 'systolic_bp', 'diastolic_bp', 'respiratory_rate', 'spo2']:
                val = int(round(val))
                if vital == 'spo2': val = min(100, val)
            elif vital == 'temperature':
                val = round(val, 1)
            vitals_dict[vital] = val
            
    if vitals_dict.get('systolic_bp') and vitals_dict.get('diastolic_bp'):
        vitals_dict['blood_pressure'] = f"{vitals_dict['systolic_bp']}/{vitals_dict['diastolic_bp']}"
    else:
        vitals_dict['blood_pressure'] = None
        
    gcs = 15
    if archetype in ['TRAUMA', 'NEUROLOGICAL'] and random.random() < 0.3:
        gcs = random.randint(3, 14)
    vitals_dict['gcs'] = gcs if random.random() >= 0.2 else None
    
    pain_scale = random.randint(5, 10) if archetype in ['TRAUMA', 'ABDOMINAL', 'CARDIAC', 'MINOR_INJURY'] else random.randint(0, 5)
    vitals_dict['pain_scale'] = pain_scale if random.random() >= 0.2 else None
    
    history_available = random.random() >= 0.5
    if not history_available:
        history = []
        
    return PatientInput(
        id=patient_id,
        name=f"Patient_{patient_id[-4:]}",
        age=age,
        gender=gender,
        chief_complaint=complaint,
        vitals=Vitals(**vitals_dict),
        history_available=history_available,
        medical_history=history,
        observed_signs=signs,
        arrival_mode=arrival_mode,
        symptoms=symptoms
    )

def generate_batch(count: int, archetype_mix: dict = None) -> list[PatientInput]:
    np.random.seed(42)
    patients = []
    
    if archetype_mix is None:
        archs = list(ARCHETYPES.keys())
        counts = [count // len(archs)] * len(archs)
        for i in range(count % len(archs)):
            counts[i] += 1
        
        mix_list = []
        for arch, c in zip(archs, counts):
            mix_list.extend([arch] * c)
    else:
        mix_list = []
        for arch, weight in archetype_mix.items():
            mix_list.extend([arch] * int(count * weight))
        while len(mix_list) < count:
            mix_list.append(random.choice(list(ARCHETYPES.keys())))
        
    random.shuffle(mix_list)
    
    for arch in mix_list[:count]:
        patients.append(generate_patient(archetype=arch))
        
    np.random.seed(None)
    return patients

def generate_outlier_patients() -> list[PatientInput]:
    return [
        PatientInput(
            id=f"SURGE_{uuid.uuid4().hex[:6].upper()}",
            name="Silent MI",
            age=62,
            gender="F",
            chief_complaint="indigestion",
            vitals=Vitals(heart_rate=88, systolic_bp=135, diastolic_bp=85, respiratory_rate=16, temperature=37.0, spo2=98, gcs=15, pain_scale=3, blood_pressure="135/85"),
            history_available=True,
            medical_history=["diabetes type 2", "hyperlipidemia"],
            observed_signs=["slightly pale"],
            arrival_mode="walk-in",
            symptoms=["nausea", "fatigue"]
        ),
        PatientInput(
            id=f"SURGE_{uuid.uuid4().hex[:6].upper()}",
            name="Pediatric meningitis",
            age=3,
            gender="M",
            chief_complaint="fussy and warm",
            vitals=Vitals(heart_rate=150, systolic_bp=95, diastolic_bp=60, respiratory_rate=35, temperature=38.5, spo2=97, gcs=14, pain_scale=4, blood_pressure="95/60"),
            history_available=True,
            medical_history=[],
            observed_signs=["neck stiffness", "lethargic"],
            arrival_mode="walk-in",
            symptoms=["poor feeding"]
        ),
        PatientInput(
            id=f"SURGE_{uuid.uuid4().hex[:6].upper()}",
            name="Geriatric sepsis",
            age=80,
            gender="F",
            chief_complaint="just not feeling well",
            vitals=Vitals(heart_rate=105, systolic_bp=90, diastolic_bp=55, respiratory_rate=22, temperature=37.8, spo2=95, gcs=14, pain_scale=0, blood_pressure="90/55"),
            history_available=True,
            medical_history=["UTI history"],
            observed_signs=["confusion"],
            arrival_mode="ambulance",
            symptoms=["weakness"]
        ),
        PatientInput(
            id=f"SURGE_{uuid.uuid4().hex[:6].upper()}",
            name="Drug seeker",
            age=30,
            gender="M",
            chief_complaint="worst pain ever",
            vitals=Vitals(heart_rate=75, systolic_bp=120, diastolic_bp=80, respiratory_rate=14, temperature=36.9, spo2=100, gcs=15, pain_scale=10, blood_pressure="120/80"),
            history_available=True,
            medical_history=["multiple ED visits"],
            observed_signs=["comfortable while unobserved"],
            arrival_mode="walk-in",
            symptoms=["diffuse pain"]
        )
    ]
