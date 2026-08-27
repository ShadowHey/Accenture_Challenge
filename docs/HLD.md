# High-Level Design (HLD)

## Project Goal
To build a simple, deterministic, and explainable clinician-facing triage prototype (Stage 1) that evaluates simulated patient data, calculates priority/uncertainty, manages a waiting queue, and allows clinician overrides.

## System Architecture
- **Frontend Layer**: Vanilla HTML/JS/CSS client offering a dashboard view of the queue and modalities for clinician override.
- **Backend API Layer**: FastAPI server orchestrating the triage process, queue management, and audit logging.
- **Triage Engine**: Pure Python logical components evaluating rules and uncertainty without ML models for transparency.
- **Data Layer**: Static JSON file for simulated patients and in-memory dicts/lists for runtime state.

## Major Data Flow
1. **Patient Intake**: Simulated patient JSON is submitted to `POST /api/triage`.
2. **Validation & Triage**: Triage Engine evaluates patient data, assigns priority (LEVEL 1-5), calculates confidence score, and determines safety escalation.
3. **Queueing**: Patient is placed in the Queue Monitor, which tracks waiting times.
4. **Monitoring**: If a patient waits too long or vitals deteriorate (`POST /api/queue/vitals`), reassessment/escalation flags are raised.
5. **Override**: A clinician can override priority (`POST /api/override`), which updates the queue and records the action in the Audit Logger.
