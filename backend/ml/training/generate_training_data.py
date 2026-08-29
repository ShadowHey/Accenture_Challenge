import os
import csv
import random
import numpy as np
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

def generate_data():
    np.random.seed(42)
    random.seed(42)
    
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Define archetypes: (name, [complaints], [signs], vitals_mean, label)
    archetypes = [
        # LEVEL 1
        ("Cardiac Arrest", ["Unresponsive", "Found down", "No pulse"], ["Cyanosis", "Apneic"], {"hr": 0, "sys": 0, "rr": 0, "spo2": 0, "gcs": 3}, "LEVEL 1"),
        ("STEMI", ["Crushing chest pain", "Chest pain radiating to jaw", "Left arm pain"], ["Diaphoretic", "Clutching chest"], {"hr": 110, "sys": 160, "rr": 24, "spo2": 96, "gcs": 15}, "LEVEL 1"),
        ("Severe Stroke", ["Sudden right side weakness", "Unable to speak", "Facial droop"], ["Aphasia", "Hemiparesis"], {"hr": 90, "sys": 190, "rr": 18, "spo2": 97, "gcs": 11}, "LEVEL 1"),
        ("Sepsis", ["Fever and confusion", "Extremely weak", "Lethargic"], ["Mottled skin", "Altered mental status"], {"hr": 130, "sys": 85, "rr": 28, "spo2": 92, "gcs": 13}, "LEVEL 1"),
        ("Major Trauma", ["High speed MVA", "Fell from 20 feet", "Gunshot wound to chest"], ["Active hemorrhage", "Unconscious"], {"hr": 140, "sys": 80, "rr": 35, "spo2": 88, "gcs": 8}, "LEVEL 1"),
        ("Respiratory Failure", ["Can't breathe", "Gasping for air", "Severe asthma attack"], ["Tripoding", "Cyanotic", "Accessory muscle use"], {"hr": 125, "sys": 140, "rr": 38, "spo2": 82, "gcs": 14}, "LEVEL 1"),
        ("Anaphylaxis", ["Throat closing", "Severe allergic reaction", "Swollen lips"], ["Stridor", "Hives", "Wheezing"], {"hr": 135, "sys": 88, "rr": 32, "spo2": 91, "gcs": 15}, "LEVEL 1"),
        ("Overdose", ["Found unresponsive with needles", "Took whole bottle of pills"], ["Pinpoint pupils", "Bradypnea"], {"hr": 55, "sys": 95, "rr": 6, "spo2": 85, "gcs": 6}, "LEVEL 1"),
        
        # LEVEL 2
        ("Mild Stroke", ["Numbness in arm", "Difficulty finding words", "Slight facial asymmetry"], ["Mild drift", "Slurred speech"], {"hr": 85, "sys": 170, "rr": 16, "spo2": 98, "gcs": 15}, "LEVEL 2"),
        ("Chest Pain", ["Tightness in chest", "Heart palpitations", "Chest pressure"], ["Anxious", "Sweaty"], {"hr": 105, "sys": 145, "rr": 20, "spo2": 97, "gcs": 15}, "LEVEL 2"),
        ("DKA", ["Vomiting for 2 days", "High blood sugar", "Extremely thirsty"], ["Fruity breath", "Dry mucous membranes", "Kussmaul breathing"], {"hr": 115, "sys": 105, "rr": 28, "spo2": 99, "gcs": 14}, "LEVEL 2"),
        ("Appendicitis", ["Severe right lower quadrant pain", "Abdominal pain and fever"], ["Guarding", "Rebound tenderness"], {"hr": 110, "sys": 130, "rr": 20, "spo2": 99, "gcs": 15}, "LEVEL 2"),
        ("GI Bleed", ["Vomiting blood", "Black tarry stools", "Dizzy when standing"], ["Pale", "Melena"], {"hr": 115, "sys": 100, "rr": 18, "spo2": 98, "gcs": 15}, "LEVEL 2"),
        ("Ectopic Pregnancy", ["Severe pelvic pain", "Vaginal bleeding and abdominal pain"], ["Pale", "Tachycardic"], {"hr": 120, "sys": 105, "rr": 22, "spo2": 98, "gcs": 15}, "LEVEL 2"),
        ("Asthma Exacerbation", ["Short of breath", "Wheezing", "Coughing fits"], ["Audible wheeze", "Tachypnea"], {"hr": 110, "sys": 135, "rr": 26, "spo2": 94, "gcs": 15}, "LEVEL 2"),
        ("Pediatric Fever High", ["Baby feels very hot", "Not eating and fever"], ["Lethargic", "Warm to touch"], {"hr": 150, "sys": 95, "rr": 35, "spo2": 98, "gcs": 15}, "LEVEL 2"),
        
        # LEVEL 3
        ("Abdominal Pain", ["Stomach ache", "Cramping", "Nausea"], ["Mild tenderness"], {"hr": 90, "sys": 125, "rr": 16, "spo2": 99, "gcs": 15}, "LEVEL 3"),
        ("Migraine", ["Worst headache", "Light sensitivity", "Throbbing pain"], ["Photophobia", "Holding head"], {"hr": 85, "sys": 140, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 3"),
        ("Fracture", ["Fell on arm", "Deformed wrist", "Ankle pain after fall"], ["Swelling", "Deformity"], {"hr": 95, "sys": 130, "rr": 18, "spo2": 99, "gcs": 15}, "LEVEL 3"),
        ("Laceration Deep", ["Cut hand with knife", "Deep laceration on leg"], ["Bleeding controlled", "2 inch laceration"], {"hr": 88, "sys": 120, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 3"),
        ("Back Pain", ["Pulled back", "Sciatica", "Lower back pain"], ["Spasm", "Pain with movement"], {"hr": 85, "sys": 135, "rr": 16, "spo2": 99, "gcs": 15}, "LEVEL 3"),
        
        # LEVEL 4
        ("Sprain", ["Twisted ankle", "Knee pain", "Rolled ankle"], ["Mild swelling", "Limping"], {"hr": 80, "sys": 120, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 4"),
        ("Minor Laceration", ["Paper cut", "Small scrape", "Abrasions"], ["Minor bleeding", "Superficial wound"], {"hr": 75, "sys": 115, "rr": 14, "spo2": 100, "gcs": 15}, "LEVEL 4"),
        ("Earache", ["Ear pain", "Stuffy ear"], ["Red tympanic membrane"], {"hr": 85, "sys": 120, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 4"),
        ("UTI", ["Pain with urination", "Frequent urination"], ["No CVA tenderness"], {"hr": 85, "sys": 125, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 4"),
        
        # LEVEL 5
        ("Medication Refill", ["Need prescription", "Lost meds"], ["Normal exam"], {"hr": 70, "sys": 110, "rr": 14, "spo2": 100, "gcs": 15}, "LEVEL 5"),
        ("Suture Removal", ["Need stitches out"], ["Well healed wound"], {"hr": 75, "sys": 115, "rr": 14, "spo2": 100, "gcs": 15}, "LEVEL 5"),
        ("Work Note", ["Need doctors note", "Missed work"], ["Normal exam"], {"hr": 70, "sys": 120, "rr": 16, "spo2": 100, "gcs": 15}, "LEVEL 5")
    ]
    
    # 25 total archetypes defined above. Let's multiply them to get to 18,000 records.
    # 18,000 / 25 = 720 per archetype.
    
    records = []
    texts_to_encode = []
    
    for arch_name, complaints, signs, vitals, label in archetypes:
        for _ in range(720):
            age = np.random.randint(18, 90)
            if "Pediatric" in arch_name:
                age = np.random.randint(1, 18)
                
            is_ped = 1 if age < 18 else 0
            is_ger = 1 if age > 65 else 0
            
            hr = max(0, int(np.random.normal(vitals["hr"], 10)))
            sys_bp = max(0, int(np.random.normal(vitals["sys"], 15)))
            dia_bp = max(0, int(sys_bp * 0.6))
            rr = max(0, int(np.random.normal(vitals["rr"], 3)))
            spo2 = min(100, max(0, int(np.random.normal(vitals["spo2"], 2))))
            temp = round(np.random.normal(37.0, 0.4), 1)
            gcs = vitals["gcs"]
            
            # Pain scale based on level
            if label == "LEVEL 1": pain = np.random.randint(0, 11)
            elif label == "LEVEL 2": pain = np.random.randint(7, 11)
            elif label == "LEVEL 3": pain = np.random.randint(4, 8)
            elif label == "LEVEL 4": pain = np.random.randint(1, 5)
            else: pain = np.random.randint(0, 3)
            
            # Random missing vitals (20% chance to miss non-critical vitals)
            missing = 0
            if np.random.rand() > 0.8 and label not in ["LEVEL 1", "LEVEL 2"]:
                hr, sys_bp, dia_bp, rr, spo2, temp = 0, 0, 0, 0, 0, 0.0
                missing = 5
                
            hist_avail = 1 if np.random.rand() > 0.3 else 0
            num_med = np.random.randint(0, 5) if hist_avail else 0
            num_signs = len(signs)
            
            arr = np.random.choice([0, 1])
            if label in ["LEVEL 1", "LEVEL 2"]: arr = 1 # ambulance
            
            c_text = random.choice(complaints)
            s_text = random.choice(signs) if signs else ""
            
            full_text = f"{c_text} {s_text}".strip().lower()
            texts_to_encode.append(full_text)
            
            # Save raw numeric data (without embeddings yet)
            row = [
                age, is_ped, is_ger, hr, sys_bp, dia_bp, rr, temp, spo2, gcs, pain,
                hist_avail, num_med, num_signs, arr, missing, label
            ]
            records.append(row)
            
    # Add Outliers (2,000 records)
    print("Generating outliers...")
    outlier_texts = []
    for _ in range(2000):
        age = np.random.randint(40, 90)
        hr, sys_bp, dia_bp, rr, spo2, temp, gcs = 80, 120, 80, 16, 99, 37.0, 15
        pain = 2
        
        # Silent MI
        c_text = "Indigestion and fatigue"
        s_text = "Slightly pale"
        full_text = f"{c_text} {s_text}".strip().lower()
        outlier_texts.append(full_text)
        
        row = [age, 0, 1 if age>65 else 0, hr, sys_bp, dia_bp, rr, temp, spo2, gcs, pain, 1, 3, 1, 0, 0, "LEVEL 2"]
        records.append(row)
        
    texts_to_encode.extend(outlier_texts)
    
    print(f"Encoding {len(texts_to_encode)} text fields...")
    embeddings = model.encode(texts_to_encode, show_progress_bar=True)
    
    print("Combining features and saving...")
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "training_data.csv")
    
    feature_names = [
        "age", "is_pediatric", "is_geriatric", "heart_rate", "sys_bp", "dia_bp",
        "respiratory_rate", "temperature", "spo2", "gcs", "pain_scale",
        "history_available", "num_medical_conditions", "num_observed_signs",
        "arrival_mode_encoded", "missing_vitals"
    ] + [f"emb_{i}" for i in range(384)] + ["label"]
    
    with open(out_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(feature_names)
        for i, row in enumerate(records):
            full_row = row[:-1] + embeddings[i].tolist() + [row[-1]]
            writer.writerow(full_row)

    print(f"Generated {len(records)} records at {out_path}")

if __name__ == "__main__":
    generate_data()
