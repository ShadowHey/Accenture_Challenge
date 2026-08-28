# Agent Working Memory — PatientTriage.ai

> **Purpose**: Contains the current project state, assumptions, architecture, completed work, known limitations, and next steps so future agent sessions can safely continue.
> **Last Updated**: 2026-08-28T06:35:00+05:30

## Current Project State
- **Stage**: Stage 2 implementation IN PROGRESS
- **Stage 1 Status**: ✅ Complete — deterministic rules, basic queue, override, audit, 20 seed patients
- **Stage 2 Status**: 🔄 Phase 0 (Documentation)

## Architecture Summary
- **Backend**: Python / FastAPI (backend/main.py is the entry point)
- **Frontend**: Vanilla HTML/JS/CSS (served by FastAPI static mount at `/`)
- **Storage**: In-memory (dicts + lists)
- **ML**: scikit-learn GradientBoosting (to be added in Phase 3)
- **Data**: JSON seed files in patient_data/seed/

## Key Architectural Decisions
1. ML model is advisory-only — deterministic rules form a safety floor
2. ML can escalate priority but NEVER downgrade below rules floor
3. Age-stratified vital thresholds: pediatric (<18), adult (18-65), geriatric (>65)
4. Vanilla JS frontend (no framework) — deliberate Stage 1 choice, preserved
5. In-memory storage — prototype scope, persistence is Stage 3

## File Layout (Stage 1)
```
patient_triage.ai/
├── backend/
│   ├── main.py           — FastAPI app, all endpoints
│   ├── models.py         — Pydantic models (PatientInput, TriageResult)
│   ├── triage_engine/
│   │   ├── triage_rules.py          — LEVEL 1-5 rules (flat thresholds)
│   │   ├── triage_explanation.py    — Orchestrator
│   │   ├── uncertainty_calculator.py — Confidence scorer
│   │   └── patient_validator.py     — Missing field checker
│   ├── queue/
│   │   └── queue_monitor.py         — QueueMonitor class
│   └── audit/
│       └── audit_logger.py          — AuditLogger class
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── patient_data/
│   ├── schemas/patient_schema.json
│   └── seed/simulated_patients.json (20 patients)
├── tests/unit/test_triage.py
├── docs/HLD.md, LLD.md
├── requirements.txt (fastapi, uvicorn, pydantic, pytest)
└── ... (README, Conversation, etc.)
```

## Files to Add in Stage 2
```
├── backend/
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── feature_extractor.py
│   │   ├── model_loader.py
│   │   ├── predictor.py
│   │   ├── reconciler.py
│   │   ├── models/triage_model.joblib
│   │   └── training/
│   │       ├── generate_training_data.py
│   │       └── train_model.py
│   └── simulation/
│       ├── __init__.py
│       ├── patient_generator.py
│       ├── surge_simulator.py
│       └── deterioration_simulator.py
├── Stage2.md, ML_ModelTraining.md, ARCHITECTURE.md, DECISIONS.md
├── ongoing_Tasks_Stage2.md, AGENT_WORKING_MEMORY.md
└── tests/unit/test_ml.py, test_queue.py, test_simulation.py
    tests/integration/test_full_pipeline.py
```

## Known Limitations
- Synthetic ML training data (no real clinical data)
- In-memory state (lost on restart)
- Keyword-based chief complaint parsing (improved but not NLP)
- Vital thresholds are approximate (not validated by clinicians)

## Important Assumptions
- Regulatory jurisdiction: HIPAA (US)
- All patient data is simulated
- Model runs in-process (no separate ML service)
- No authentication/authorization in prototype
- scikit-learn available locally (pip install)

## Next Steps
- Complete Phase 0 → Phase 1 → ... → Phase 10
- See `ongoing_Tasks_Stage2.md` for detailed progress
