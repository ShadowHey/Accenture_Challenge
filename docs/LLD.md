# Low-Level Design (LLD)

## ML Pipeline

### Feature Extraction (`backend/ml/feature_extractor.py`)
- **Inputs**: `PatientInput` schema containing demographic, vitals, and text fields (chief complaint, observed signs).
- **Processing**:
  - Replaces rudimentary keyword flag extraction with `SentenceTransformer` (`all-MiniLM-L6-v2`) embeddings.
  - Generates a 384-dimensional vector from a concatenated string of `chief_complaint` and `observed_signs`.
  - Combines NLP embeddings with structured numeric data (age, vitals, boolean flags).
- **Outputs**: 400-dimensional numeric vector (16 structured features + 384 embedding features).

### Reconciler (`backend/ml/reconciler.py`)
- **Logic**: 
  - Compares deterministic rule-based output against ML predictions.
  - **Fallback/Safety Mechanism**: If the ML model's prediction confidence is less than 60% (`< 0.60`), the system assigns the predicted rule-based priority but changes the overall status to `CLINICIAN_REVIEW_REQUIRED`.

### Model Training (`backend/ml/training/generate_training_data.py`)
- Uses 25 specific clinical archetypes to generate highly realistic synthetic tabular data with correlated textual fields.
- Uses `SentenceTransformer` during dataset generation to export the 384-dimensional vectors directly to `training_data.csv`.

## Triage Engine (`backend/triage_engine/triage_rules.py`)
- **Deterministic Rules**: Contains highly-specific, age-adjusted rules for vitals thresholds:
  - **Pediatric (<18)**: Fine-grained HR and RR thresholds based on age subsets (e.g., <2y, 2-5y, 6-12y, 13-17y).
  - **Adult (18-65)**: Standard clinical vitals thresholds.
  - **Geriatric (>65)**: Tighter thresholds for vitals to account for frailty (e.g., SpO2 <94%, Temp >38.0°C).
- Identifies critical extremes (e.g., hypothermia, bradypnea) mapped immediately to Level 1.

## Frontend
- **Patient Addition (`frontend/app.js`, `frontend/index.html`)**: Allows UI toggling between a standard Web Form and a JSON text editor.
- The JSON view iterates over an array of parsed objects, validating required fields (`name`, `age`, `gender`, `chief_complaint`) before triggering multiple concurrent `POST /patient` API requests.

### Presentation Layer (Queue Dashboard)
- Introduced a **Horizontal Queue** component to complement the vertical list view. It provides an at-a-glance ticker of waiting patients with interactive tooltips dynamically positioned via JavaScript to prevent UI clipping and improve spatial efficiency.

### NLP Conversational Parsing (`backend/nlp_parser.py`)
- **Inputs**: Natural language strings from the Rhea UI chatbot (e.g., "The patient's spo2 is 94 and hr 120").
- **Processing**:
  - Uses Regex to pull out numerical values.
  - Strips stop words and fuzzy-matches (`difflib`) the remaining context words against a dictionary of known vital synonyms (e.g., "sats" -> "spo2").
- **Outputs**: A mapped dictionary of structured vitals that can be immediately patched into the patient's record.

## Hospital Integration & Ingestion Pipeline

### FHIR Parser Adapter (`backend/adapters/fhir_parser.py`)
- **Inputs**: Standard FHIR R4 Bundle JSON containing `Patient`, `Observation`, and `Condition` resource types.
- **Processing**:
  - Extracts demographics (`name`, `gender`, `birthDate` $\rightarrow$ calculated `age`).
  - Maps standard LOINC codes into internal vital fields:
    - `8867-4`: Heart Rate (bpm)
    - `2708-6`: SpO2 (%)
    - `8310-5`: Body Temperature (°F/°C)
    - `9279-1`: Respiratory Rate (breaths/min)
    - `72514-3`: Pain Scale (0–10)
    - `85354-9`: Blood Pressure (extracts systolic `8480-6` and diastolic `8462-4` components)
  - Extracts clinical conditions (`Condition` resources) into `medical_history` and `chief_complaint`.
- **Outputs**: Internal `PatientInput` dictionary with validated schema.

### Server-Side FHIR Fetcher (`backend/routers/fhir.py`)
- **Endpoint**: `POST /api/fhir/fetch-and-submit`
- **Request Model**:
  ```python
  class FHIRFetchRequest(BaseModel):
      fhir_url: HttpUrl
  ```
- **Security**: Protected by `get_hospital_code` dependency (validates JWT Bearer session token).
- **Network Flow**:
  1. Executes server-to-server HTTP GET to `fhir_url` with 10.0-second timeout and `Accept: application/fhir+json`.
  2. Avoids client-side CORS limitations and shields external FHIR server endpoints from browser inspection.
  3. Translates bundle via `parse_fhir_bundle()`.
  4. Resolves authenticated hospital ID from Supabase `hospitals` table.
  5. Persists structured record to `historical_records` table linked via foreign key `hospital_id`.

### Hospital Admin Portal (`frontend/hospital_portal.html`, `frontend/hospital_portal.js`)
- **Two-Column Layout**:
  - **Left Column**: Forms for authentication (Login/Register), direct FHIR bundle JSON upload, and server-side URL fetch trigger.
  - **Right Column (API Reference)**: Persistent sticky developer sidebar with auto-populated cURL commands (matching current origin `window.location.host`), LOINC lookup table, and 1-click clipboard copy buttons for high-frequency automated polling (~10 req/s).

