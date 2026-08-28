# High Level Design (HLD)

## Architecture Overview
PatientTriage.ai operates as a monolithic web application composed of a FastAPI backend and a vanilla JavaScript frontend. For Stage 2, the backend has been significantly expanded into a hybrid architecture.

### Core Components
1. **API Layer (`backend/main.py`)**: Central entry point. Orchestrates incoming requests, triggers the triage pipeline, interacts with the queue, and logs to the audit engine.
2. **Triage Rules Engine (`backend/triage_engine/`)**: Deterministic rules-based system. Uses age-stratified thresholds (Pediatric, Adult, Geriatric) to establish a guaranteed safety floor.
3. **ML Module (`backend/ml/`)**: Advisory layer using a trained `scikit-learn` GradientBoostingClassifier. Extracts a 22-dimensional feature vector, runs local inference, and suggests a priority.
4. **Reconciler**: Enforces the primary safety invariant: The ML model is permitted to escalate severity (e.g., LEVEL 3 → LEVEL 2) based on subtle patterns, but is strictly prohibited from downgrading severity below the rules-established floor.
5. **Queue Engine V2 (`backend/queue/`)**: Active queue management. Tracks patient wait times against severity-specific thresholds and detects vital sign deterioration to flag required reassessments.
6. **Simulation Engine (`backend/simulation/`)**: Procedurally generates synthetic patients based on clinical archetypes, simulates surge events, and injects clinical deterioration into waiting patients.
7. **Audit Logger (`backend/audit/`)**: Comprehensive event ledger recording all triage decisions, re-triages, clinician overrides, and ML-vs-Rules disagreements.

## Data Flow (Triage Pipeline)
1. **Input**: `PatientInput` arrives via API.
2. **Validation**: Missing fields identified. String fields (like BP) parsed.
3. **Rules Evaluation**: Priority assigned based strictly on vital sign thresholds and chief complaint keywords. Uncertainty calculated.
4. **ML Inference**: Features extracted, model predicts priority.
5. **Reconciliation**: Final priority = `min(rules_priority, ml_priority)` (lower number = higher severity).
6. **Logging**: Full context logged to audit. Result added to queue.
