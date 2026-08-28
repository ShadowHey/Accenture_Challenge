# Project Map

## Backend

*   `backend/main.py`: FastAPI server setup, API routes (Stage 2: full hybrid pipeline, simulation endpoints, queue management).
*   `backend/models.py`: Pydantic data models (`PatientInput`, `Vitals`, `TriageResult`, etc.). Expanded for Stage 2.
*   `backend/triage_engine/`
    *   `triage_rules.py`: Age-stratified deterministic logic for assigning priority levels.
    *   `uncertainty_calculator.py`: Logic for measuring missing information and calculating confidence/escalation.
    *   `patient_validator.py`: Logic for checking data completeness.
    *   `triage_explanation.py`: Orchestrator for the rules portion of the pipeline.
*   `backend/ml/` (Stage 2)
    *   `feature_extractor.py`: Extracts 22-dimensional feature vector from PatientInput.
    *   `model_loader.py`: Singleton loader for the joblib model.
    *   `predictor.py`: Executes local ML inference.
    *   `reconciler.py`: Merges rules and ML predictions safely.
    *   `training/generate_training_data.py`: Generates synthetic CSV data.
    *   `training/train_model.py`: Trains GradientBoostingClassifier and saves to joblib.
*   `backend/queue/`
    *   `queue_monitor.py`: Queue manager. Tracks severity thresholds, active reassessment, and vitals trend monitoring.
*   `backend/audit/`
    *   `audit_logger.py`: In-memory ledger tracking triage, overrides, deterioration, and disagreements.
*   `backend/simulation/` (Stage 2)
    *   `patient_generator.py`: Generates synthetic patients using archetypes.
    *   `surge_simulator.py`: Manages surge volume and threshold adjustments.
    *   `deterioration_simulator.py`: Injects vitals deterioration into waiting patients.

## Frontend

*   `frontend/index.html`: UI structure (Stage 2: modals for Add Patient, Override, Update Vitals, stats panel).
*   `frontend/app.js`: UI logic and API communication.
*   `frontend/style.css`: UI styling and animations.

## Patient Data

*   `patient_data/schemas/patient_schema.json`: JSON Schema for validation.
*   `patient_data/seed/simulated_patients.json`: Pre-defined patients for legacy testing and surge mixing.

## Tests

*   `tests/unit/test_triage.py`: Comprehensive test suite for rules, ML features, reconciler, and queue thresholds.

## Documentation

*   `README.md`: Project summary and run instructions.
*   `docs/stage1/`: Contains original HLD, LLD, and summaries from Stage 1.
*   `docs/stage2/`: Contains updated HLD, LLD, `ARCHITECTURE.md`, `DECISIONS.md`, and `ML_ModelTraining.md` for Stage 2.
*   `ProjectMap.md`: File map (this file).
*   `Conversation.md`: Log of key accomplishments.
