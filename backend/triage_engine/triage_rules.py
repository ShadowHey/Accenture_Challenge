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
    severe_keywords = ['chest pain', 'severe', 'stroke', 'hemorrhage', 'weakness', 'droop', 'slurred', 'neurological', 'cva']
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

    # GCS check (age-adjusted safety margin)
    if gcs is not None:
        if age_group in ['GERIATRIC', 'PEDIATRIC'] and gcs < 10:
            reasons.append(f"Critical GCS for vulnerable patient: {gcs}")
            is_level_1 = True
        elif age_group == 'ADULT' and gcs < 9:
            reasons.append(f"Critical GCS: {gcs}")
            is_level_1 = True

    # SpO2 check (age-adjusted safety margin)
    if spo2 is not None:
        if age_group in ['GERIATRIC', 'PEDIATRIC'] and spo2 < 88:
            reasons.append(f"Critical SpO2 for vulnerable patient: {spo2}%")
            is_level_1 = True
        elif age_group == 'ADULT' and spo2 < 85:
            reasons.append(f"Critical SpO2: {spo2}%")
            is_level_1 = True

    # Heart rate check (age-adjusted extremes)
    if hr is not None:
        if age_group == 'PEDIATRIC':
            if (age < 2 and hr > 180) or (2 <= age <= 5 and hr > 160) or \
               (6 <= age <= 12 and hr > 140) or (13 <= age <= 17 and hr > 130):
                reasons.append(f"Critical high HR for pediatric ({age}y): {hr} bpm")
                is_level_1 = True
            if (age < 2 and hr < 60) or (age >= 2 and hr < 60):
                reasons.append(f"Critical low HR for pediatric ({age}y): {hr} bpm")
                is_level_1 = True
        elif age_group == 'ADULT':
            if hr > 160:
                reasons.append(f"Critical high HR for adult: {hr} bpm")
                is_level_1 = True
            if hr < 40:
                reasons.append(f"Critical low HR for adult: {hr} bpm")
                is_level_1 = True
        elif age_group == 'GERIATRIC':
            if hr > 140:
                reasons.append(f"Critical high HR for geriatric: {hr} bpm")
                is_level_1 = True
            if hr < 45:
                reasons.append(f"Critical low HR for geriatric: {hr} bpm")
                is_level_1 = True

    # Temperature check (only infants and severe hypothermia are L1)
    if temp is not None:
        if temp < 35.0:
            reasons.append(f"Critical hypothermia: {temp}°C")
            is_level_1 = True
        elif age_group == 'PEDIATRIC' and age < 2 and temp > 39.0:
            reasons.append(f"Critical high temp for infant: {temp}°C")
            is_level_1 = True

    # Respiratory rate check (extremes only)
    if rr is not None:
        if age_group == 'PEDIATRIC':
            if (age < 2 and (rr > 60 or rr < 15)) or \
               (2 <= age <= 12 and (rr > 50 or rr < 12)) or \
               (13 <= age < 18 and (rr > 40 or rr < 10)):
                reasons.append(f"Critical RR for pediatric ({age}y): {rr}")
                is_level_1 = True
        elif age_group == 'ADULT':
            if rr > 35 or rr < 8:
                reasons.append(f"Critical RR for adult: {rr}")
                is_level_1 = True
        elif age_group == 'GERIATRIC':
            if rr > 30 or rr < 10:
                reasons.append(f"Critical RR for geriatric: {rr}")
                is_level_1 = True

    # Systolic BP check (Shock limits)
    if sys_bp is not None:
        if age_group in ['ADULT', 'GERIATRIC'] and sys_bp < 80:
            reasons.append(f"Critical low systolic BP: {sys_bp} mmHg")
            is_level_1 = True
        elif age_group == 'PEDIATRIC':
            if (age < 1 and sys_bp < 60) or (1 <= age <= 10 and sys_bp < 70) or (age > 10 and sys_bp < 80):
                reasons.append(f"Critical low systolic BP for pediatric ({age}y): {sys_bp} mmHg")
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
        if age_group == 'PEDIATRIC':
            if (age < 2 and hr > 160) or (2 <= age <= 5 and hr > 140) or \
               (6 <= age <= 12 and hr > 120) or (13 <= age <= 17 and hr > 110):
                reasons.append(f"Elevated HR for pediatric ({age}y): {hr} bpm")
                is_level_2 = True
            elif (age >= 2 and hr < 80):
                reasons.append(f"Low HR for pediatric ({age}y): {hr} bpm")
                is_level_2 = True
        elif age_group == 'ADULT':
            if hr > 120 or hr < 60:
                reasons.append(f"Abnormal HR for adult: {hr} bpm")
                is_level_2 = True
        elif age_group == 'GERIATRIC':
            if hr > 110 or hr < 60:
                reasons.append(f"Abnormal HR for geriatric: {hr} bpm")
                is_level_2 = True

    if spo2 is not None:
        if spo2 < 92:
            reasons.append(f"Concerning SpO2: {spo2}%")
            is_level_2 = True

    if temp is not None:
        if temp < 36.0:
            reasons.append(f"Concerning hypothermia: {temp}°C")
            is_level_2 = True
        elif age_group == 'PEDIATRIC' and temp > 38.5:
            reasons.append(f"Concerning temp for pediatric: {temp}°C")
            is_level_2 = True
        elif age_group == 'ADULT' and temp > 39.0:
            reasons.append(f"Concerning temp for adult: {temp}°C")
            is_level_2 = True
        elif age_group == 'GERIATRIC' and temp > 38.5:
            reasons.append(f"Concerning temp for geriatric: {temp}°C")
            is_level_2 = True

    if rr is not None:
        if age_group == 'PEDIATRIC':
            if (age < 2 and rr > 40) or (2 <= age <= 12 and rr > 30) or \
               (13 <= age < 18 and rr > 24):
                reasons.append(f"Concerning RR for pediatric ({age}y): {rr}")
                is_level_2 = True
        elif age_group == 'ADULT' and (rr > 22 or rr < 12):
            reasons.append(f"Concerning RR for adult: {rr}")
            is_level_2 = True
        elif age_group == 'GERIATRIC' and (rr > 22 or rr < 12):
            reasons.append(f"Concerning RR for geriatric: {rr}")
            is_level_2 = True

    if sys_bp is not None:
        if 80 <= sys_bp <= 100:
            reasons.append(f"Borderline low systolic BP: {sys_bp} mmHg")
            is_level_2 = True
        elif sys_bp >= 160:
            reasons.append(f"Severe hypertension: {sys_bp} mmHg")
            is_level_2 = True

    if gcs is not None and gcs < 15:
        reasons.append(f"Altered mental status (GCS): {gcs}")
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
