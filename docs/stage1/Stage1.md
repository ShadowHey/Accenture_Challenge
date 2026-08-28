# Stage 1 Implementation Summary

## Stage Objective
Build a simple, deterministic, explainable prototype of a clinician-facing triage application handling simulated patient intake, priority evaluation, uncertainty, a waiting queue, and clinician override.

## What Was Implemented
- **Data Engine**: A seed script with 20 simulated diverse patients.
- **Triage Engine**: Deterministic Python rules assigning LEVEL 1-5, calculating confidence (0-1), providing plain-text reasons, and enforcing safety escalation (upgrading priority on high uncertainty).
- **Queue System**: In-memory queue monitoring wait time thresholds (flags for reassessment) and vital updates (flags for escalation).
- **Audit System**: In-memory logger tracking clinician priority overrides.
- **API/Server**: FastAPI backend exposing the core engine.
- **Frontend**: Vanilla HTML/JS dashboard displaying the queue, showing explanation reasons, and allowing overrides and vitals simulation.
- **Surge Simulation**: An endpoint that loads all simulated patients simultaneously and lowers queue wait thresholds to quickly simulate an overwhelmed department.

## Decisions Made
- **Python/FastAPI**: Chosen for the backend for its simplicity, fast routing, and Pydantic validation (which perfectly fits strict data contracts).
- **Vanilla JS**: Kept the frontend dependency-free to align with the "simplest working prototype" requirement without bringing in React/Vue boilerplate.
- **In-Memory Storage**: State is entirely in RAM (queue dict, audit list) as persistence is out-of-scope for the core logic demonstration of Stage 1.

## Important Tradeoffs
- Simple heuristic rules vs. complex medical logic. The rules are hardcoded and non-exhaustive, solely to demonstrate the system flow.
- Time simulation. Queue wait threshold is artificially low (60s normally, 10s in surge) to make demonstration easy without waiting hours.

## Tests Performed
- Basic pytest unit tests for priority evaluation and uncertainty math.

## What We Should Improve Later (Stage 2+)
- Extract hardcoded triage rules into a configurable DSL or database.
- Transition in-memory state to a database (PostgreSQL/Redis) for persistence and multi-worker deployment.
- Integrate real or advanced machine-learning-based uncertainty models instead of heuristic decrements.
- Implement robust patient authentication and authorization.
- Enhance the UI/UX with a proper frontend framework.
