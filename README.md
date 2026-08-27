# PatientTriage.ai

A prototype for emergency-department patient triage. 

This repository contains **Stage 1** of the prototype, focusing on a simple, deterministic, and explainable core workflow. It serves as a proof-of-concept for automated triage logic, queue management, and safety escalations.

## Currently Supported Functionalities

- **Simulated Patient Intake**: Accepts and validates simulated patient data (vitals, symptoms, age, etc.). Includes a diverse seed dataset of 20 patients (pediatric, geriatric, zero-history, etc.).
- **Deterministic Triage Engine**: Assigns priority from LEVEL 1 (Immediate) to LEVEL 5 (Non-Urgent) based on configurable, understandable heuristic rules.
- **Uncertainty & Safety Escalation**: Calculates a confidence score based on missing fields or vague symptoms. Automatically escalates the priority level if there is high clinical uncertainty for a potentially concerning presentation.
- **Explainable Decisions**: Generates plain-text reasons for the assigned priority and uncertainty levels, ensuring transparent decision support.
- **Queue Management**: An in-memory waiting queue that monitors wait times. Automatically flags patients for **REASSESSMENT** if they wait beyond a specific threshold, or **ESCALATION** if their vitals deteriorate.
- **Clinician Override**: Allows a clinician to override the system's recommended priority level and requires a textual reason.
- **Audit Logging**: Maintains an immutable log of all clinician overrides for accountability.
- **Surge Simulation**: A built-in mode to instantly load the queue with 20 patients and lower wait thresholds, demonstrating how the system behaves during an emergency department surge.

## Local Setup Instructions

Follow these steps to run the prototype on your local machine.

### Prerequisites
- **Python 3.8+** installed on your system.

### 1. Clone/Navigate to the Repository
Open your terminal and navigate to the project folder:
```bash
cd patient_triage.ai
```

### 2. Create a Virtual Environment
It's recommended to use a virtual environment to isolate dependencies:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3. Install Dependencies
Install the required packages (`fastapi`, `uvicorn`, `pydantic`):
```bash
pip install -r requirements.txt
```

### 4. Run the Server
Start the FastAPI server using Uvicorn:
```bash
uvicorn backend.main:app --reload
```

### 5. Open the Application
Open your web browser and go to:
**[http://127.0.0.1:8000](http://127.0.0.1:8000)**

## How to Use the Prototype
1. **Surge Mode**: Click the **"Simulate Surge (Load Patients)"** button on the top right to instantly populate the waiting queue with 20 simulated patients.
2. **Review Patients**: Observe how different patients are triaged into Levels 1-5, and read the "Reasons" to understand the engine's logic.
3. **Queue Monitoring**: Wait a few seconds to see the "Wait Time" increase. Patients waiting too long will receive a yellow `REASSESSMENT REQUIRED` badge.
4. **Update Vitals**: Click **"Update Vitals"** on any patient and enter worsening vitals (e.g., HR > 120 or SpO2 < 94) to see a red `ESCALATION REQUIRED` badge appear.
5. **Clinician Override**: Click **"Clinician Override"**, select a new priority, and provide a reason. The change will reflect in the queue, and the action will be permanently recorded in the **Audit Log** section on the right.

## Documentation
- For a complete map of the folders and files, see **[ProjectMap.md](ProjectMap.md)**.
- For architectural details, see **[docs/HLD.md](docs/HLD.md)** and **[docs/LLD.md](docs/LLD.md)**.
- For a summary of Stage 1 decisions and trade-offs, see **[Stage1.md](Stage1.md)**.
