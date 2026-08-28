# ML Model Training Guide — PatientTriage.ai

## Overview

PatientTriage.ai uses a **Gradient Boosted Trees** classifier (scikit-learn `GradientBoostingClassifier`) as an advisory decision-support layer alongside deterministic triage rules. This document explains the complete training pipeline, data strategy, model decisions, and future directions.

## Architecture

```
PatientInput → Feature Extractor → [22 numeric features] → GBM Model → (predicted_level, confidence, importances)
                                                                              ↓
                                                              Reconciler (merge with rules floor)
                                                                              ↓
                                                              Final TriageResult
```

## Training Data Strategy

### Why Synthetic Data?
Real clinical data (e.g., MIMIC-III) requires:
- Data Use Agreements and IRB approval
- Complex ETL from clinical data formats
- De-identification verification

For this prototype, we generate synthetic training data that:
- Covers all three age populations (pediatric, adult, geriatric)
- Includes all clinical archetypes (chest pain, respiratory, trauma, etc.)
- Has controlled noise to simulate real-world variability
- Produces reproducible results with a fixed random seed

### Data Generation Process

**Script**: `backend/ml/training/generate_training_data.py`

1. **Define clinical archetypes** — 8 categories:
   - Cardiac (chest pain, MI symptoms)
   - Respiratory (SOB, asthma, COPD exacerbation)
   - Trauma (MVA, falls, penetrating injuries)
   - Pediatric fever/infection
   - Geriatric fall/hip fracture
   - Abdominal (appendicitis, bowel obstruction)
   - Neurological (stroke, seizure, altered consciousness)
   - Minor (cuts, sprains, rashes)

2. **For each archetype**, generate patients with:
   - Vitals drawn from clinically plausible distributions (mean ± std)
   - Age sampled from appropriate range
   - Missing data introduced randomly (~20% of records miss some vitals)
   - History availability randomized (50/50 per brief)
   - Ground truth labels assigned based on clinical rules + expert heuristics

3. **Label assignment**:
   - LEVEL 1: Critical vitals OR unresponsive OR major trauma with shock
   - LEVEL 2: Seriously abnormal vitals OR severe symptoms
   - LEVEL 3: Moderately abnormal OR painful presentation
   - LEVEL 4: Minor injury, stable vitals
   - LEVEL 5: Non-urgent, normal vitals

4. **Volume**: ~2000 records (250 per archetype)

5. **Split**: 80% train, 20% test (stratified by label)

## Feature Engineering

| # | Feature | Type | Description |
|---|---|---|---|
| 1 | age | int | Patient age in years |
| 2 | is_pediatric | binary | 1 if age < 18 |
| 3 | is_geriatric | binary | 1 if age > 65 |
| 4 | heart_rate | int | BPM (0 if missing) |
| 5 | systolic_bp | int | mmHg (0 if missing) |
| 6 | diastolic_bp | int | mmHg (0 if missing) |
| 7 | respiratory_rate | int | breaths/min (0 if missing) |
| 8 | temperature | float | °C (0 if missing) |
| 9 | spo2 | int | % (0 if missing) |
| 10 | gcs | int | Glasgow Coma Scale 3-15 (0 if missing) |
| 11 | pain_scale | int | 0-10 (0 if missing) |
| 12 | history_available | binary | 1 if patient has prior records |
| 13 | num_medical_conditions | int | len(medical_history) |
| 14 | num_observed_signs | int | len(observed_signs) |
| 15 | arrival_mode_encoded | int | 0=walk-in, 1=ambulance, 2=helicopter |
| 16 | complaint_severity_score | int | Keyword-based severity 0-3 |
| 17 | num_missing_vitals | int | Count of None vitals fields |
| 18 | is_chest_pain | binary | Chief complaint contains chest pain |
| 19 | is_respiratory | binary | Chief complaint is respiratory |
| 20 | is_trauma | binary | Chief complaint is trauma |
| 21 | is_neurological | binary | Chief complaint is neurological |
| 22 | is_abdominal | binary | Chief complaint is abdominal |

**Missing value handling**: Missing vitals are encoded as 0 (not imputed). The `num_missing_vitals` feature explicitly captures missingness as a signal — more missing data → higher uncertainty.

## Model Training

**Script**: `backend/ml/training/train_model.py`

### Hyperparameters
```python
GradientBoostingClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    min_samples_split=10,
    min_samples_leaf=5,
    random_state=42
)
```

**Rationale**: 
- 100 trees: sufficient for 22 features, fast inference
- max_depth=4: prevents overfitting to synthetic patterns
- min_samples_leaf=5: ensures no leaf represents a single outlier

### Training Steps
```bash
# 1. Generate synthetic training data
python -m backend.ml.training.generate_training_data

# 2. Train and evaluate the model
python -m backend.ml.training.train_model

# 3. Model is saved to backend/ml/models/triage_model.joblib
```

### Evaluation Metrics
The training script produces:
- **Classification report** (precision, recall, F1 per class)
- **Confusion matrix**
- **Overall accuracy**
- **Feature importance ranking**

### Expected Performance
On synthetic test data, expect:
- Overall accuracy: ~85-92% (synthetic data is well-structured)
- LEVEL 1 recall: >95% (critical cases must not be missed)
- LEVEL 5 precision: >90% (avoid clogging queue with false non-urgent)

## How to Retrain on New Data

### With More Synthetic Data
```bash
# Edit generate_training_data.py to add more archetypes or volume
python -m backend.ml.training.generate_training_data
python -m backend.ml.training.train_model
```

### With Real Clinical Data (Future)
1. **Obtain data**: Apply for MIMIC-III/IV access or use hospital EHR exports
2. **Map fields**: Ensure your data has the 22 feature fields (or subsets with missing value handling)
3. **Create a CSV** with columns matching the feature names above + a `label` column (LEVEL 1-5)
4. **Modify `train_model.py`** to read your CSV instead of synthetic data:
   ```python
   df = pd.read_csv("your_clinical_data.csv")
   ```
5. **Re-train**: `python -m backend.ml.training.train_model`
6. **Validate**: Check that LEVEL 1 recall is >95% before deploying

### Important Considerations for Real Data
- **De-identification**: Remove all PHI (names, dates, MRNs) before training
- **Label quality**: Ensure labels come from experienced triage nurses, not just billing codes
- **Population balance**: Real ED data is typically 5% LEVEL 1, 15% LEVEL 2, 30% LEVEL 3, 30% LEVEL 4, 20% LEVEL 5. Stratify your splits.
- **Temporal validation**: Train on earlier data, test on later data to detect distribution shift
- **Bias audit**: Check model performance across age groups, genders, and racial demographics

## Model Safety Design

### The ML model is NOT the final authority
- Deterministic rules compute a "safety floor" priority
- ML computes an advisory priority
- The **Reconciler** takes the MORE SEVERE of the two
- ML can **escalate** but **never downgrade** below the rules floor
- All disagreements are logged in the audit trail

### Failure Modes
| Failure | Behavior |
|---|---|
| Model file missing | System runs in rules-only mode, logs warning |
| Model file corrupt | System runs in rules-only mode, logs error |
| Feature extraction error | System runs in rules-only mode for that patient |
| Model predicts nonsense | Rules floor catches it; disagreement logged |

## Future Directions

1. **MIMIC-III training**: Swap synthetic data for real clinical data
2. **SHAP explanations**: Add per-prediction SHAP values for deeper interpretability
3. **Online learning**: Update model weights as clinician overrides accumulate
4. **Calibrated probabilities**: Use Platt scaling for well-calibrated confidence scores
5. **Multi-output model**: Predict (severity, expected_disposition, time_sensitivity) jointly
6. **Ensemble**: Combine GBM with logistic regression for robustness
7. **Federated learning**: Train across hospitals without sharing raw data
