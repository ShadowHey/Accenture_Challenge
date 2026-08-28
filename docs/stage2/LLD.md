# Low Level Design (LLD)

## Directory Structure
```
backend/
├── audit/              # AuditLogger (singleton)
├── ml/                 # ML inference, feature extraction, model loading, reconciler
│   ├── models/         # Stored joblib model
│   └── training/       # Synthetic data generation and training scripts
├── queue/              # QueueMonitor (singleton), active reassessment tracking
├── simulation/         # Patient generator, surge control, deterioration logic
└── triage_engine/      # Deterministic age-stratified rules, uncertainty calculation
```

## Key Classes & Models (Pydantic)
- **`Vitals`**: Enhanced with `systolic_bp`, `diastolic_bp`, `gcs`, `pain_scale`.
- **`PatientInput`**: Enhanced with `arrival_mode`, `symptoms`, `history_available`.
- **`TriageResult`**: Captures both rules output (`rules_priority`) and ML output (`ml_priority`, `ml_confidence`, `feature_importances`), plus reconciliation `source` and `disagreement` notes.

## Triage Logic & Thresholds
- **Age Stratification**: Patients are divided into `PEDIATRIC` (<18), `ADULT` (18-65), and `GERIATRIC` (>65). Thresholds are uniquely tuned (e.g., >130 HR is critical for geriatric, but normal for a crying infant).
- **Uncertainty**: Confidence drops for missing vitals (-0.08 each), missing history (-0.15), and ambiguous symptoms. High uncertainty or critically low GCS forces an automatic 1-level priority escalation.

## Reconciler Logic
```python
def reconcile(rules_priority, rules_confidence, ml_priority, ml_confidence):
    rules_num = extract_num(rules_priority)
    ml_num = extract_num(ml_priority)
    if ml_num < rules_num:
        return ml_priority, 'ML_ESCALATED', "Explanation"
    return rules_priority, 'RULES_FLOOR', "Explanation"
```

## Simulation Mechanics
- **Patient Generation**: 8 distinct clinical archetypes (Cardiac, Trauma, Pediatric Fever, etc.) dictate base vital sign distributions and typical missingness rates.
- **Surge**: `create_surge_patients` injects 3× normal volume. `QueueMonitor` shifts wait-time thresholds to 50% of normal capacity.
- **Deterioration**: `simulate_deterioration` randomly selects ~15% of queued patients, shifting their vitals negatively (e.g., +20 HR, -5% SpO2), which triggers a forced re-triage via the API layer.
