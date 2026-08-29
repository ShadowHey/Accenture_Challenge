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
