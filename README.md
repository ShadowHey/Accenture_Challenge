# PatientTriage.ai

**Stage 2 Implementation — Hybrid Triage & Simulation**

PatientTriage.ai is an intelligent patient triage assistant designed to help hospital emergency departments prioritize and route patients as they arrive. The system uses a hybrid approach: a deterministic age-stratified rules engine establishes a safety floor, while a locally run Machine Learning (ML) model provides advisory severity predictions. 

## Key Features

1. **Hybrid Triage Engine**: Combines strict deterministic rules (age-stratified vitals) with an ML advisory layer. The reconciler strictly enforces safety invariants (ML can escalate severity, but never downgrade below rules).
2. **Surge Simulation**: Simulates an influx of patients and halves the wait-time thresholds to model capacity strains.
3. **Deterioration Modeling**: Simulates patients worsening while waiting in the queue, automatically triggering re-triage.
4. **Enhanced Audit & Queue**: Active queue management tracks wait times against severity thresholds. Comprehensive audit logging covers triage, overrides, deterioration, and ML-Rules disagreements.

## Architecture

- **Backend**: FastAPI (Python), providing REST endpoints.
- **Frontend**: Vanilla HTML/JS/CSS served directly by FastAPI.
- **Machine Learning**: `scikit-learn` GradientBoostingClassifier running locally (no cloud dependency).
- **Data Storage**: In-memory data structures (Queue, Audit logs) for prototype simplicity.

## Running the Application

### 1. Set up the Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Generate Data & Train Model
```bash
python -m backend.ml.training.generate_training_data
python -m backend.ml.training.train_model
```

### 3. Start the Server
```bash
uvicorn backend.main:app --reload
```

## Documentation Structure

To ensure clarity on how decisions were made across different phases of the challenge, the documentation is divided by stage:

- **`docs/stage1/`**: Contains the original High-Level Design (HLD) and Low-Level Design (LLD) from Stage 1.
- **`docs/stage2/`**: Contains the updated HLD, LLD, Architecture invariants, ML Training instructions, and Architectural Decisions (`DECISIONS.md`) taken for Stage 2.
- **`Conversation.md`**: Provides a running log of accomplishments across both stages.

## Interaction Flow
1. Load Seed Patients or add a new patient via the UI form.
2. The system evaluates the patient via the rules engine and ML model, reconciling the final priority.
3. Trigger a Surge to see how the system handles high volume.
4. Simulate Deterioration to watch vitals change and auto-escalate waiting patients.
5. Review the Audit log to analyze system vs. ML disagreements and clinician overrides.
