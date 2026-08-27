# Project Map

This file documents the core folders and files for PatientTriage.ai.

## Folders

### `backend/`
- **What this folder does**: Contains the Python server, triage logic, queue, and audit systems.
- **Why it exists**: Separates server-side logic from the client.
- **Which part of the pipeline**: Core processing layer.
- **What it connects to**: Exposed via REST API to the frontend.

### `frontend/`
- **What this folder does**: Contains the Vanilla HTML/JS/CSS client application.
- **Why it exists**: Provides the clinician-facing UI for input and overrides.
- **Which part of the pipeline**: The user interface layer.
- **What it connects to**: Calls the backend API.

### `patient_data/`
- **What this folder does**: Contains JSON schemas and simulated patient data.
- **Why it exists**: Provides the deterministic dataset required for the prototype.
- **Which part of the pipeline**: Data input/seeding.
- **What it connects to**: Loaded by the backend/tests.

### `tests/`
- **What this folder does**: Contains test suites.
- **Why it exists**: Ensures rules and uncertainty logic behave correctly.

### `docs/`
- **What this folder does**: Contains high-level and low-level design documents.
- **Why it exists**: Architectural reference.

## Files

### `README.md`
- **What**: High-level overview of the project.
- **Why**: Standard entry point for any developer.

### `Conversation.md`
- **What**: Permanent log of developer and agent interactions.
- **Why**: Allows tracking how decisions evolved over time.

### `changes.md`
- **What**: A log of significant file-level changes.
- **Why**: History of what changed and why.

### `ProjectMap.md`
- **What**: Map of the project (this file).
- **Why**: Quick onboard for new developers.

*(This file will be updated as we add more implementation files.)*
