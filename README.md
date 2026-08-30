# PatientTriage.ai

**Stage 2 Implementation — Hybrid Triage & Simulation**

PatientTriage.ai is an intelligent patient triage assistant designed to help hospital emergency departments prioritize and route patients as they arrive. The system uses a hybrid approach: a deterministic age-stratified rules engine establishes a safety floor, while a locally run Machine Learning (ML) model provides advisory severity predictions. 

## Key Features

1. **Hybrid Triage Engine**: Combines strict deterministic rules (age-stratified vitals) with an ML advisory layer. The reconciler strictly enforces safety invariants (ML can escalate severity, but never downgrade below rules).
2. **Natural Language Processing (NLP)**: Extracts structured vital signs from unstructured conversational text using advanced Regex and fuzzy matching, speeding up data entry for clinicians.
3. **Surge Simulation**: Simulates an influx of patients and halves the wait-time thresholds to model capacity strains.
4. **Deterioration Modeling**: Simulates patients worsening while waiting in the queue, automatically triggering re-triage.
5. **Enhanced Audit & Queue**: Active queue management tracks wait times against severity thresholds. Comprehensive audit logging covers triage, overrides, deterioration, and ML-Rules disagreements.
6. **Multi-Tenant Architecture**: Supports Role-Based Access Control (RBAC) with secure login for Hospital Admins, Clinicians, and Receptionists.

## Architecture

- **Backend**: FastAPI (Python), providing REST endpoints.
- **Frontend**: Vanilla HTML/JS/CSS served directly by FastAPI, featuring an interactive queue and an AI Chatbot UI (Rhea).
- **Machine Learning**: `scikit-learn` GradientBoostingClassifier running locally utilizing NLP embeddings via `SentenceTransformer`.
- **Database**: Supabase (PostgreSQL) for structured patient data and multi-tenant hospital configurations.

---

## 🚀 Getting Started: Step-by-Step Guide

Follow these instructions to download, configure, and run PatientTriage.ai locally.

### 1. Clone the Repository
```bash
git clone https://github.com/ShadowHey/Accenture_Challenge.git
cd Accenture_Challenge
```

### 2. Set up the Environment
Ensure you have Python 3.9+ installed. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Database Configuration
The system uses Supabase (PostgreSQL) to store data.
1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```
2. Open the `.env` file and add your Supabase credentials:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_KEY=your_supabase_api_key
   ```
3. Initialize your Supabase database by running the SQL script located at `database_migration_hospitals.sql` in your Supabase SQL Editor. This will create the required tables and insert default hospital records.

### 4. Generate Data & Train Model
Train the local Machine Learning model with synthetic data (this requires NLP embeddings generation and may take a moment):
```bash
python -m backend.ml.training.generate_training_data
python -m backend.ml.training.train_model
```

### 5. Start the Server
Run the FastAPI backend server:
```bash
uvicorn backend.main:app --reload
```
Once the server is running, you can access the application in your browser:
- **Triage Dashboard (Clinician/Reception)**: [http://127.0.0.1:8000/login.html](http://127.0.0.1:8000/login.html)
- **Hospital Admin Portal**: [http://127.0.0.1:8000/hospitals](http://127.0.0.1:8000/hospitals)

---

## 🔑 Example Login Credentials

To try out the system, we have pre-configured example accounts for different roles. You can use these credentials to log into the portals:

### Hospital Admin Portal
Access the [Admin Portal](http://127.0.0.1:8000/hospitals) to manage your hospital's system:
- **Hospital A**:
  - Hospital Code: `H001`
  - Password: `A001`
- **Hospital B**:
  - Hospital Code: `H002`
  - Password: `B002`

### Triage Dashboard (Emergency Department)
Access the [Staff Login](http://127.0.0.1:8000/login.html) for day-to-day triage operations:

**Hospital H001 Staff:**
- **Clinician Login**:
  - Username: `clinician@H001.hosp`
  - Password: `clinician123`
- **Receptionist Login**:
  - Username: `receptionist@H001.hosp`
  - Password: `reception123`

**Hospital H002 Staff:**
- **Clinician Login**:
  - Username: `clinician@H002.hosp`
  - Password: `clinician123`
- **Receptionist Login**:
  - Username: `receptionist@H002.hosp`
  - Password: `reception123`

---

## 🛠️ How to Use the System

1. **Log in**: Choose a role (Clinician or Receptionist) and log into the Triage Dashboard.
2. **Add Patients**: Use the "Add Patient" form or JSON bulk upload to input patient data.
3. **Automated Triage**: The system will evaluate the patient via the rules engine and ML model, then assign a reconciled priority. Cases with high ML uncertainty will be flagged for `CLINICIAN_REVIEW_REQUIRED`.
4. **NLP Chatbot (Rhea)**: Use the chat interface to naturally type patient vitals (e.g., "Patient has HR 120 and Temp 39"). The NLP engine will parse and update the patient's record automatically.
5. **Simulate Scenarios**:
   - **Trigger a Surge**: Use the surge controls to see how the system handles high patient volume and adjusts wait-time thresholds.
   - **Simulate Deterioration**: Watch vitals worsen over time and see the system auto-escalate waiting patients to higher priorities.
6. **Review Logs**: Check the audit trail to analyze system vs. ML disagreements and any clinician overrides.

## Documentation Structure

To ensure clarity on how decisions were made across different phases of the challenge, the documentation is divided by stage:

- **`docs/stage1/`**: Contains the original High-Level Design (HLD) and Low-Level Design (LLD) from Stage 1.
- **`docs/stage2/`**: Contains the updated HLD, LLD, Architecture invariants, ML Training instructions, and Architectural Decisions (`DECISIONS.md`) taken for Stage 2.
- **`Conversation.md`**: Provides a running log of accomplishments across both stages.
- **`changes.md`**: Tracks granular code-level updates and rationale.
