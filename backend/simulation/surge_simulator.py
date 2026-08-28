import random
from backend.simulation.patient_generator import generate_batch, generate_outlier_patients

def create_surge_patients(multiplier: int = 3, base_count: int = 20):
    total_count = multiplier * base_count
    
    patients = generate_batch(total_count)
    outliers = generate_outlier_patients()
    
    patients.extend(outliers)
    random.shuffle(patients)
    
    return patients

def get_surge_thresholds() -> dict:
    return {
        'LEVEL 1': 0,
        'LEVEL 2': 300,
        'LEVEL 3': 900,
        'LEVEL 4': 1800,
        'LEVEL 5': 3600
    }

def get_normal_thresholds() -> dict:
    return {
        'LEVEL 1': 0,
        'LEVEL 2': 600,
        'LEVEL 3': 1800,
        'LEVEL 4': 3600,
        'LEVEL 5': 7200
    }
