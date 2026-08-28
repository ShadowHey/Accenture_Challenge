import os
import csv
import random
import numpy as np
from backend.ml.feature_extractor import FEATURE_NAMES

def generate_data():
    np.random.seed(42)
    random.seed(42)
    
    archetypes = [
        "cardiac", "respiratory", "trauma", "pediatric_fever", 
        "geriatric_fall", "abdominal", "neurological", "minor_injury"
    ]
    
    records = []
    
    for arch in archetypes:
        for _ in range(250):
            age = np.random.randint(18, 65)
            hr = np.random.normal(80, 15)
            sys_bp = np.random.normal(120, 15)
            dia_bp = np.random.normal(80, 10)
            rr = np.random.normal(16, 2)
            temp = np.random.normal(37.0, 0.5)
            spo2 = np.random.normal(98, 1)
            gcs = 15
            pain = np.random.randint(0, 5)
            arr = 0
            sev = 0
            chest = 0
            resp = 0
            trauma = 0
            neuro = 0
            abd = 0
            label = "LEVEL 5"
            
            if arch == "cardiac":
                age = np.random.randint(40, 90)
                hr = np.random.normal(110, 20)
                sys_bp = np.random.normal(150, 30)
                chest = 1
                sev = 2
                label = "LEVEL 2"
                if np.random.rand() < 0.1:
                    label = "LEVEL 1"
                    sev = 3
                    gcs = np.random.randint(3, 13)
            elif arch == "respiratory":
                rr = np.random.normal(24, 4)
                spo2 = np.random.normal(92, 4)
                resp = 1
                sev = 2
                label = "LEVEL 2"
                if spo2 < 90:
                    label = "LEVEL 1"
            elif arch == "trauma":
                trauma = 1
                pain = np.random.randint(5, 11)
                sev = 2
                arr = np.random.choice([0, 1, 2], p=[0.2, 0.6, 0.2])
                label = "LEVEL 2" if arr > 0 else "LEVEL 3"
            elif arch == "pediatric_fever":
                age = np.random.randint(1, 18)
                temp = np.random.normal(39.5, 0.5)
                hr = np.random.normal(120, 15)
                sev = 1
                label = "LEVEL 3"
            elif arch == "geriatric_fall":
                age = np.random.randint(65, 100)
                trauma = 1
                pain = np.random.randint(3, 8)
                label = "LEVEL 3"
            elif arch == "abdominal":
                abd = 1
                pain = np.random.randint(4, 9)
                sev = 1
                label = "LEVEL 3"
            elif arch == "neurological":
                neuro = 1
                gcs = np.random.randint(10, 15)
                sev = 3 if gcs < 13 else 2
                label = "LEVEL 2" if gcs >= 13 else "LEVEL 1"
            elif arch == "minor_injury":
                trauma = 1
                pain = np.random.randint(1, 4)
                label = "LEVEL 4"
                if np.random.rand() < 0.2:
                    label = "LEVEL 5"

            hr = int(hr) if np.random.rand() > 0.2 else 0
            sys_bp = int(sys_bp) if np.random.rand() > 0.2 else 0
            dia_bp = int(dia_bp) if np.random.rand() > 0.2 and sys_bp > 0 else 0
            rr = int(rr) if np.random.rand() > 0.2 else 0
            temp = round(temp, 1) if np.random.rand() > 0.2 else 0.0
            spo2 = min(100, int(spo2)) if np.random.rand() > 0.2 else 0
            
            missing_vitals = sum(1 for v in [hr, sys_bp, rr, temp, spo2] if v == 0)
            
            hist = 1 if np.random.rand() > 0.5 else 0
            med_cond = np.random.randint(0, 4) if hist else 0
            obs_signs = np.random.randint(0, 3)

            is_ped = 1 if age < 18 else 0
            is_ger = 1 if age > 65 else 0
            
            record = [
                age, is_ped, is_ger, hr, sys_bp, dia_bp, rr, temp, spo2, gcs, pain,
                hist, med_cond, obs_signs, arr, sev, missing_vitals,
                chest, resp, trauma, neuro, abd, label
            ]
            records.append(record)

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data.csv")
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(FEATURE_NAMES + ["label"])
        writer.writerows(records)

    print(f"Generated {len(records)} records at {out_path}")

if __name__ == "__main__":
    generate_data()
