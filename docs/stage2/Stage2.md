# Stage 2 Implementation Summary

## Stage Objective
Evolve the Stage 1 deterministic prototype into a hybrid rules+ML triage system with age-differentiated scoring, active queue re-assessment, realistic surge simulation, patient deterioration modeling, and a local ML model — all while maintaining the safety-first design and clinician authority.

## What Stage 2 Adds Over Stage 1

### 1. Hybrid Triage Pipeline (Rules + ML)
- **Deterministic rules** remain as the safety floor (never bypassed)
- **Gradient Boosted Trees ML model** provides advisory risk scoring
- **Reconciler** merges both: ML can escalate, never downgrade
- **Disagreement logging**: when rules and ML differ, it's recorded and shown

### 2. Age-Differentiated Scoring
- Separate vital sign threshold tables for pediatric (<18), adult (18-65), geriatric (>65)
- A fever of 38.5°C is treated differently in a 3-year-old vs a 75-year-old
- Age group displayed on every patient card

### 3. Local ML Model
- scikit-learn GradientBoostingClassifier (22 features, ~100 trees)
- Trained on ~2000 synthetic patient records
- Ships as a <1MB joblib file — runs locally, no GPU, no cloud
- Feature importances provided per prediction for explainability
- Falls back to rules-only mode if model is unavailable

### 4. Active Queue Re-Assessment
- Severity-based wait thresholds (LEVEL 1: immediate, LEVEL 2: 10min, etc.)
- When threshold exceeded: full re-triage (rules + ML), not just a flag
- Vitals deterioration triggers automatic re-triage
- Surge mode halves all thresholds

### 5. Realistic Surge Simulation
- Generates ~60 new patients from 8 clinical archetypes (3× base volume)
- Patients are diverse: different ages, complaints, vital profiles
- Pre-designed outlier patients (ambiguous, deceptive presentations)

### 6. Patient Deterioration Simulation
- Manual trigger to simulate vitals worsening in waiting patients
- 10-20% of patients randomly deteriorate per cycle
- Deterioration triggers full re-triage pipeline

### 7. Add Patient via UI
- Form modal with all schema fields (name, age, vitals, complaint, etc.)
- Auto-generates patient ID
- Patient immediately triaged and added to queue

### 8. Comprehensive Audit Trail
- Logs ALL events: triage, re-assessment, override, disagreement, deterioration, surge
- Each event includes timestamp, patient_id, event_type, details
- Expanded audit display in frontend

### 9. Enhanced Frontend
- Dashboard statistics panel (counts per level, avg wait, ML agreement %)
- Enhanced patient cards (ML vs rules scores, age group badge, trend indicators)
- Surge controls (start/stop)
- Discharge button
- Deterioration simulation button
- ML confidence bar per patient

## Decisions Made
See `DECISIONS.md` for the complete decision log.

## Key Safety Guarantees
1. ML is advisory-only — deterministic rules form an inviolable safety floor
2. ML can escalate but NEVER downgrade below the rules floor
3. High uncertainty automatically escalates priority
4. Missing patient data escalates (never assumes "normal")
5. Clinician can always override — logged with mandatory reason
6. Model failure → graceful fallback to rules-only mode

## Tests
- Unit tests: age-stratified rules, ML feature extraction, reconciler safety invariant, queue thresholds
- Integration tests: full pipeline from intake through queue through override
- ML evaluation: classification report on held-out test set

## What Could Improve Further (Stage 3+)
- Database persistence (PostgreSQL/Redis)
- Real clinical training data (MIMIC-III/IV)
- SHAP per-prediction explanations
- Authentication and role-based access control
- Background automatic deterioration (asyncio tasks)
- WebSocket real-time updates (replace polling)
- Multi-hospital configuration profiles
