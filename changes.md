# Changelog

## 2026-08-29
### Code Changes
- **`backend/ml/feature_extractor.py`**: Refactored feature extraction. Integrated `SentenceTransformer` ('all-MiniLM-L6-v2') to generate 384-dimensional text embeddings for chief complaints and observed signs. Replaced hardcoded keyword-based binary flags with NLP embeddings.
  - **Why**: To capture the nuanced semantic meaning of free-text medical notes instead of relying on brittle keyword matching.
  - **Impact**: ML model can now understand complex clinical presentations better.
  - **Tests**: None explicitly added, manually verified during generation of synthetic data.
- **`backend/ml/models/triage_model.joblib`**: Updated ML model trained on the new embedding-based feature set.
- **`backend/ml/reconciler.py`**: Added logic to flag for `CLINICIAN_REVIEW_REQUIRED` if the ML model's confidence is below 60%.
  - **Why**: Ensure patient safety by having human-in-the-loop for uncertain predictions.
  - **Impact**: Reduces risk of mis-triage when the model is uncertain.
- **`backend/ml/training/generate_training_data.py`**: Overhauled synthetic data generation. Added 25 detailed clinical archetypes, generated outliers, and integrated SentenceTransformer embeddings to output features to `training_data.csv`.
  - **Why**: Generate high-quality, realistic training data with NLP embeddings for the new model architecture.
  - **Impact**: Better representation of real-world cases, resulting in a more robust model.
- **`backend/triage_engine/triage_rules.py`**: Refined rule-based thresholds for temperature, HR, RR, systolic BP, SpO2 with age-adjusted logic (Pediatric, Adult, Geriatric) for Level 1 and Level 2 severity.
  - **Why**: Standardize triage rules based on clinical guidelines for different age groups.
  - **Impact**: Increased accuracy and safety of the deterministic rule engine.
- **`frontend/app.js` & `frontend/index.html`**: Added a UI toggle in the "Add Patient" modal to support single form entry and JSON bulk upload.
  - **Why**: To allow users (and testers) to easily input multiple patients at once or copy-paste clinical scenarios in JSON format.
  - **Impact**: Improves UX and testing efficiency.

### Code Changes (Update - 9:00 AM)
- **`frontend/index.html`**, **`frontend/app.js`**, **`frontend/style.css`**: Added a horizontal scrolling queue component (`#horizontal-queue-container`) with shared tooltips to visually represent waiting patients above the standard list view.
  - **Why**: To provide a space-efficient, at-a-glance view of the waiting room triage queue for clinicians and administrators.
  - **Impact**: Enhances dashboard usability and situational awareness in high-volume surge scenarios.
  - **Tests**: Manually tested frontend rendering and tooltip positioning.

### Code Changes (Update - 2:45 PM)
- **`backend/nlp_parser.py`** [NEW]: Created a natural language processing module that extracts structured vital signs (HR, BP, SpO2, Temp, RR) from unstructured conversational text using Regex and fuzzy matching (`difflib`).
  - **Why**: To allow clinicians to quickly update patient vitals by typing naturally instead of filling out rigid forms.
  - **Impact**: Dramatically speeds up data entry and integrates seamlessly with the Rhea Chatbot.
- **`backend/main.py`**: Added new API endpoints to handle Rhea AI chatbot interactions and route text to the `nlp_parser`.
- **`frontend/app.js`, `frontend/index.html`, `frontend/style.css`**: Integrated the 'Rhea' AI Chatbot UI into the dashboard. Added interactive Queue Filters to allow sorting patients by priority level (L1-L5) or 'Clinician Review'.
  - **Why**: To improve dashboard usability. Clinicians need to immediately filter the queue during surges or rapidly update vitals via chat.
  - **Impact**: Provides a major UX improvement and makes the system feel more intelligent and responsive.
- **`tests/unit/test_triage.py`**: Updated unit tests to accurately validate the newly refined age-stratified rules and 400-dimension ML features.

## 2026-09-01
### Code Changes (Hospital Portal FHIR Ingestion & cURL API Reference)
- **`backend/routers/fhir.py`**:
  - Added new endpoint `POST /api/fhir/fetch-and-submit` with `FHIRFetchRequest` Pydantic model (`fhir_url: HttpUrl`).
  - Added server-side HTTP fetching using `httpx.Client(timeout=10.0)` to pull FHIR bundles directly from external hospital FHIR servers, parse them via `parse_fhir_bundle()`, and insert into Supabase `historical_records`.
  - Added robust exception handling for `httpx.TimeoutException` (504), `httpx.HTTPStatusError` (502), and `FHIRParserError` (400).
  - **Why**: Allows hospital admins to ingest FHIR records simply by supplying their server endpoint rather than manually copy-pasting massive JSON payloads.
  - **Impact**: Removes manual data entry friction, improves ingestion throughput, and eliminates browser-level CORS issues by executing the fetch server-side.
  - **Tests**: Verified syntax, request validation, and endpoint integration.

- **`requirements.txt`**:
  - Added `httpx` dependency.
  - **Why**: Required for asynchronous/synchronous server-side HTTP calls to external FHIR endpoints.
  - **Impact**: Enables server-to-server healthcare data fetching.

- **`frontend/hospital_portal.html`**:
  - Redesigned the page layout from a single narrow column to a responsive two-column grid (`.page-layout`, `.left-col`, `.right-col`).
  - Added a "Fetch from FHIR Server URL" input section below the existing JSON textarea, separated by an "OR" divider.
  - Built a persistent, sticky dark-themed **API Reference sidebar** (`.api-ref`) on the right containing ready-to-run cURL snippets for:
    1. Authentication (`POST /api/auth/login`)
    2. Direct FHIR bundle submission (`POST /api/fhir/historical`)
    3. Server-side URL fetching (`POST /api/fhir/fetch-and-submit`)
    4. Supported LOINC codes reference table for vital signs
    5. Best practices and rate-limiting tips for high-frequency polling (~10 req/s).
  - Added "Copy" buttons to every code block.
  - **Why**: Empowers external hospital IT teams and integration scripts to programmatically ingest historical data at high frequency without guessing payload structures or authentication flows.
  - **Impact**: Greatly improves developer experience and integration efficiency.

- **`frontend/hospital_portal.js`**:
  - Added `buildCurlSnippets()` IIFE that dynamically populates cURL commands with the active `window.location.host` origin.
  - Added `copyCode()` clipboard handler with temporary visual feedback ("Copied!").
  - Added event listener for `#fhir-fetch-btn` with input validation, JWT token authorization header, and loading state management ("Fetching...").
  - **Why**: Provides automated feedback and 1-click developer onboarding.
  - **Impact**: Clean, interactive UX for both web-based and terminal-based hospital integrations.

