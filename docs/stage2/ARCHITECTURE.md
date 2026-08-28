# Architecture — PatientTriage.ai (Stage 2)

## System Overview

PatientTriage.ai is a hybrid rules+ML triage decision-support system for emergency departments. It uses deterministic safety rules as an inviolable floor, with a local ML model providing advisory escalation. All decisions are explainable, auditable, and overridable by clinicians.

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       FRONTEND (Vanilla JS)                     │
│   Dashboard │ Add Patient │ Surge Controls │ Stats │ Audit Log  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API (JSON)
┌──────────────────────────▼──────────────────────────────────────┐
│                       BACKEND (FastAPI)                          │
│                                                                  │
│  ┌────────────────── TRIAGE PIPELINE ──────────────────────┐     │
│  │  1. Validator → 2. Rules Engine → 3. ML Scorer          │     │
│  │                         ↓                ↓               │     │
│  │              4. Reconciler (max severity wins)           │     │
│  │                         ↓                                │     │
│  │              5. Final TriageResult                       │     │
│  └──────────────────────────────────────────────────────────┘     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Queue Engine │  │ Simulation   │  │ Audit Engine          │   │
│  │ (priority    │  │ Engine       │  │ (all events)          │   │
│  │  queue +     │  │ (patient gen │  │                       │   │
│  │  active      │  │  + surge     │  │                       │   │
│  │  reassess)   │  │  + deterior) │  │                       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌─────────────────── DATA LAYER ──────────────────────────┐     │
│  │  In-memory: queue (dict), audit (list), ML model (joblib)│    │
│  │  Seed: patient_data/seed/simulated_patients.json         │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Patient Intake
```
User submits patient (form or seed) 
  → POST /api/patient or POST /api/triage
  → Validator checks fields, identifies missing data
  → Rules Engine evaluates age-stratified thresholds → rules_level
  → ML Scorer extracts features, predicts → ml_level, ml_confidence
  → Reconciler: final_level = min(rules_level_num, ml_level_num)
  → TriageResult created with full explainability
  → Patient added to Queue with TriageResult
  → Triage event logged in Audit
  → Response returned to frontend
```

### Queue Monitoring
```
GET /api/queue
  → Queue Engine checks all patients:
     - Wait time vs severity-based threshold?
     - Vitals worsened since last check?
  → If threshold exceeded → full re-triage (not just flag)
  → If vitals worsened → full re-triage
  → Sorted by priority then wait time
  → Response with all patients + statuses
```

### Clinician Override
```
POST /api/override
  → Clinician selects new priority + provides reason
  → Old priority preserved in audit
  → New priority applied
  → Override event logged with full context
```

### Surge Simulation
```
POST /api/surge/start
  → Patient generator creates 60 patients from archetypes
  → All triaged through full pipeline
  → Wait thresholds halved
  → Surge mode flag set
```

## Safety Invariants

1. **ML cannot downgrade**: `final_level ≤ rules_level` (lower number = higher severity)
2. **High uncertainty → escalate**: If confidence < 0.5, priority bumps by 1 level
3. **Missing data → escalate**: Zero-history + missing vitals → minimum LEVEL 3
4. **Threshold breach → re-triage**: Active re-assessment, not passive flagging
5. **Clinician authority**: Override is always allowed, always logged, never blocked

## Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | Python 3.8+ / FastAPI | Fast, typed, async-capable |
| ML | scikit-learn GBM | Local, no GPU, explainable |
| Serialization | Pydantic | Strict data contracts |
| Frontend | Vanilla HTML/JS/CSS | Zero build tooling |
| Storage | In-memory dicts/lists | Prototype simplicity |
| Testing | pytest | Standard Python testing |

## Regulatory Compliance (HIPAA)

- All data is simulated — no real PHI
- Audit trail is immutable (append-only list)
- Every decision has a documented reason
- Clinician overrides require mandatory justification
- All events timestamped
- Designed for future integration with access control and encryption
