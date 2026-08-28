from backend.models import PatientInput

def get_age_group(age: int) -> str:
    """Categorize patient by age group for threshold selection."""
    if age < 18:
        return 'PEDIATRIC'
    elif age <= 65:
        return 'ADULT'
    else:
        return 'GERIATRIC'

def evaluate_priority(patient: PatientInput) -> tuple:
    """
    Evaluates patient to determine priority level (LEVEL 1 to LEVEL 5)
    using age-stratified vital sign thresholds.
    Returns (priority, reasons, age_group).
    """
    age = patient.age
    age_group = get_age_group(age)
    reasons = []

    # Extract vitals from the nested Vitals object
    hr = patient.vitals.heart_rate
    spo2 = patient.vitals.spo2
    temp = patient.vitals.temperature
    rr = patient.vitals.respiratory_rate
    gcs = patient.vitals.gcs
    pain = patient.vitals.pain_scale

    # Parse systolic BP — try structured field first, then parse string
    sys_bp = patient.vitals.systolic_bp
    if sys_bp is None and patient.vitals.blood_pressure:
        try:
            sys_bp = int(patient.vitals.blood_pressure.split('/')[0])
        except (ValueError, IndexError):
            pass

    # Build combined text for keyword matching
    cc = (patient.chief_complaint or "").lower()
    signs_text = " ".join(patient.observed_signs).lower() if patient.observed_signs else ""
    combined_text = cc + " " + signs_text

    # Keyword categories for symptom-based assessment
    critical_keywords = ['unresponsive', 'unconscious', 'seizure', 'not breathing', 'cardiac arrest']
    severe_keywords = ['chest pain', 'severe', 'stroke', 'hemorrhage']
    moderate_keywords = ['pain', 'fracture', 'dizziness', 'vomiting']
    minor_keywords = ['sprain', 'minor', 'cut', 'rash', 'sore throat']

    # Collect critical keyword matches
    for kw in critical_keywords:
        if kw in combined_text:
            reasons.append(f"Critical symptom identified: {kw}")

    for kw in severe_keywords:
        if kw in combined_text:
            reasons.append(f"Severe symptom identified: {kw}")

    # ========================
    # LEVEL 1 CHECKS (Critical)
    # ========================
    is_level_1 = False

    # GCS check (age-adjusted)
    if gcs is not None:
        if age_group == 'GERIATRIC' and gcs < 13:
            reasons.append(f"Critical GCS for geriatric patient: {gcs}")
            is_level_1 = True
        elif gcs < 12:
            reasons.append(f"Critical GCS: {gcs}")
            is_level_1 = True

    # SpO2 check (age-adjusted)
    if spo2 is not None:
        if age_group == 'GERIATRIC' and spo2 < 92:
            reasons.append(f"Critical SpO2 for geriatric patient: {spo2}%")
            is_level_1 = True
        elif spo2 < 90:
            reasons.append(f"Critical SpO2: {spo2}%")
            is_level_1 = True

    # Heart rate check (age-adjusted with pediatric sub-ranges)
    if hr is not None:
        if age_group == 'PEDIATRIC':
            if (age < 2 and hr > 180) or (2 <= age <= 5 and hr > 160) or \
               (6 <= age <= 12 and hr > 140) or (13 <= age <= 17 and hr > 130):
                reasons.append(f"Critical high HR for pediatric ({age}y): {hr} bpm")
                is_level_1 = True
            if (age < 2 and hr < 60) or (age >= 2 and hr < 70):
                reasons.append(f"Critical low HR for pediatric ({age}y): {hr} bpm")
                is_level_1 = True
        elif age_group == 'ADULT':
            if hr > 150:
                reasons.append(f"Critical high HR for adult: {hr} bpm")
                is_level_1 = True
            if hr < 50:
                reasons.append(f"Critical low HR for adult: {hr} bpm")
                is_level_1 = True
        elif age_group == 'GERIATRIC':
            if hr > 130:
                reasons.append(f"Critical high HR for geriatric: {hr} bpm")
                is_level_1 = True
            if hr < 50:
                reasons.append(f"Critical low HR for geriatric: {hr} bpm")
                is_level_1 = True

    # Temperature check (age-adjusted — geriatric has lower threshold)
    if temp is not None:
        if age_group == 'PEDIATRIC' and temp > 39.0:
            reasons.append(f"Critical high temp for pediatric: {temp}°C")
            is_level_1 = True
        elif age_group == 'ADULT' and temp > 39.5:
            reasons.append(f"Critical high temp for adult: {temp}°C")
            is_level_1 = True
        elif age_group == 'GERIATRIC' and temp > 38.5:
            reasons.append(f"Critical high temp for geriatric: {temp}°C (lower threshold)")
            is_level_1 = True

    # Respiratory rate check (age-adjusted with pediatric sub-ranges)
    if rr is not None:
        if age_group == 'PEDIATRIC':
            if (age < 2 and rr > 50) or (2 <= age <= 12 and rr > 40) or \
               (13 <= age < 18 and rr > 30):
                reasons.append(f"Critical high RR for pediatric ({age}y): {rr}")
                is_level_1 = True
        elif age_group == 'ADULT' and rr > 28:
            reasons.append(f"Critical high RR for adult: {rr}")
            is_level_1 = True
        elif age_group == 'GERIATRIC' and rr > 26:
            reasons.append(f"Critical high RR for geriatric: {rr}")
            is_level_1 = True

    # Systolic BP check
    if sys_bp is not None:
        if sys_bp < 90:
            reasons.append(f"Critical low systolic BP: {sys_bp} mmHg")
            is_level_1 = True
        elif sys_bp > 180:
            reasons.append(f"Critical high systolic BP: {sys_bp} mmHg")
            is_level_1 = True

    if is_level_1 or any(kw in combined_text for kw in critical_keywords):
        if not reasons:
            reasons.append("Critical presentation based on symptoms and vital signs.")
        return ("LEVEL 1", reasons, age_group)

    # ========================
    # LEVEL 2 CHECKS (Emergent)
    # ========================
    is_level_2 = False

    if hr is not None:
        if age_group == 'ADULT' and hr > 120:
            reasons.append(f"Elevated HR for adult: {hr} bpm")
            is_level_2 = True
        elif age_group == 'GERIATRIC' and hr > 110:
            reasons.append(f"Elevated HR for geriatric: {hr} bpm")
            is_level_2 = True

    if spo2 is not None:
        if age_group == 'ADULT' and spo2 < 94:
            reasons.append(f"Concerning SpO2 for adult: {spo2}%")
            is_level_2 = True

    if temp is not None:
        if age_group == 'ADULT' and temp > 38.5:
            reasons.append(f"Concerning temp for adult: {temp}°C")
            is_level_2 = True

    if rr is not None:
        if age_group == 'ADULT' and rr > 22:
            reasons.append(f"Concerning RR for adult: {rr}")
            is_level_2 = True

    if pain is not None and pain >= 8:
        reasons.append(f"Severe pain: {pain}/10")
        is_level_2 = True

    if is_level_2 or any(kw in combined_text for kw in severe_keywords):
        if not reasons:
            reasons.append("Emergent presentation based on symptoms.")
        return ("LEVEL 2", reasons, age_group)

    # ========================
    # LEVEL 3 CHECKS (Urgent)
    # ========================
    is_level_3 = False

    if pain is not None and 5 <= pain < 8:
        reasons.append(f"Moderate pain: {pain}/10")
        is_level_3 = True

    if any(kw in combined_text for kw in moderate_keywords):
        if not reasons:
            reasons.append("Urgent presentation based on symptoms.")
        is_level_3 = True

    if is_level_3:
        return ("LEVEL 3", reasons, age_group)

    # ========================
    # LEVEL 4 CHECKS (Less Urgent)
    # ========================
    is_level_4 = False

    if pain is not None and 1 <= pain < 5:
        reasons.append(f"Mild pain: {pain}/10")
        is_level_4 = True

    if any(kw in combined_text for kw in minor_keywords):
        if not reasons:
            reasons.append("Minor presentation.")
        is_level_4 = True

    if is_level_4:
        return ("LEVEL 4", reasons, age_group)

    # ========================
    # LEVEL 5 (Non-Urgent)
    # ========================
    if not reasons:
        reasons.append("Vitals stable and complaint does not indicate urgent risk.")
    return ("LEVEL 5", reasons, age_group)
