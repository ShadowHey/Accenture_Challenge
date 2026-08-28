# Stage 2 — Ongoing Tasks Checkpoint

> **Purpose**: Durable checkpoint so any agent or developer can see exactly what has been completed and resume from the right point.
> **Last Updated**: 2026-08-28T06:35:00+05:30

## Phase 0: Documentation Foundation
- [x] Create `ongoing_Tasks_Stage2.md` (this file)
- [x] Create `AGENT_WORKING_MEMORY.md`
- [x] Create `DECISIONS.md`
- [x] Create `ARCHITECTURE.md`
- [x] Create `Stage2.md`
- [x] Create `ML_ModelTraining.md`
- [x] Update `Conversation.md`

## Phase 1: Data Model Extension
- [x] Extend `Vitals` model (systolic_bp, diastolic_bp, gcs, pain_scale)
- [x] Extend `PatientInput` model (arrival_mode, symptoms)
- [x] Extend `TriageResult` model (rules_priority, ml_priority, ml_confidence, age_group, source, disagreement)
- [x] Update `patient_schema.json`
- [x] Update `simulated_patients.json` with new fields + add outlier patients
- [x] Update `requirements.txt`

## Phase 2: Rules Engine V2
- [x] Create age-stratified vital sign threshold tables
- [x] Refactor `triage_rules.py` with age-differentiated scoring
- [x] Add structured symptom category scoring
- [x] Enhance `uncertainty_calculator.py` with age-adjusted uncertainty
- [x] Update `triage_explanation.py` to populate new TriageResult fields
- [x] Update `patient_validator.py` for new fields

## Phase 3: ML Module
- [x] Create `backend/ml/__init__.py`
- [x] Create `backend/ml/feature_extractor.py`
- [x] Create `backend/ml/model_loader.py`
- [x] Create `backend/ml/predictor.py`
- [x] Create `backend/ml/reconciler.py`
- [x] Create `backend/ml/training/generate_training_data.py`
- [x] Create `backend/ml/training/train_model.py`
- [x] Generate synthetic training data
- [x] Train model and save `triage_model.joblib`

## Phase 4: Queue Engine V2
- [x] Implement severity-based wait thresholds
- [x] Implement active re-triage (not just flagging)
- [x] Add vitals history tracking per patient
- [x] Add deterioration trend detection
- [x] Surge-mode threshold reduction

## Phase 5: Simulation Engine
- [x] Create `backend/simulation/patient_generator.py`
- [x] Create `backend/simulation/surge_simulator.py`
- [x] Create `backend/simulation/deterioration_simulator.py`
- [x] Add pre-designed outlier patients

## Phase 6: API Layer V2
- [x] `POST /api/patient` — add single patient via form
- [x] `POST /api/surge/start` — start 3× surge simulation
- [x] `POST /api/surge/stop` — stop surge, restore thresholds
- [x] `GET /api/stats` — dashboard statistics
- [x] `POST /api/simulate/deteriorate` — trigger deterioration cycle
- [x] `POST /api/queue/{patient_id}/discharge` — remove patient
- [x] Wire up ML into triage pipeline
- [x] Wire up simulation engine

## Phase 7: Frontend V2
- [x] Add Patient form modal + submission logic
- [x] Enhanced patient cards (ML vs rules, age group, trend indicators)
- [x] Stats panel (counts per level, avg wait, ML agreement %)
- [x] Surge controls (start/stop buttons)
- [x] Discharge button on patient cards
- [x] ML confidence bar per patient
- [x] Deterioration simulation button
- [x] Visual reassessment pulse indicators

## Phase 8: Audit V2
- [x] Expand audit to log all event types
- [x] Add event_type enum
- [x] Log triage decisions, re-assessments, disagreements, deterioration events
- [x] Enhanced audit display in frontend

## Phase 9: Testing
- [x] Unit tests: age-stratified rules
- [x] Unit tests: ML feature extraction
- [x] Unit tests: ML prediction shape
- [x] Unit tests: reconciler safety invariant
- [x] Unit tests: queue severity thresholds
- [x] Unit tests: patient generation
- [x] Integration test: full pipeline

## Phase 10: Docs & Polish
- [x] Update `README.md` for Stage 2
- [x] Update `docs/HLD.md`
- [x] Update `docs/LLD.md`
- [x] Update `ProjectMap.md`
- [x] Final verification — full flow test
