# Architectural Decisions Log — PatientTriage.ai

## Decision Record Format
Each decision follows: Problem → Alternatives → Choice → Rationale → Tradeoffs → Consequences

---

## D001: ML Model Type
**Problem**: Need a local ML model for triage risk scoring.
**Alternatives**:
1. Gradient Boosted Trees (scikit-learn GradientBoostingClassifier)
2. Random Forest (scikit-learn)
3. Small neural network (PyTorch)
4. Logistic Regression
5. XGBoost

**Choice**: Gradient Boosted Trees (scikit-learn)
**Rationale**: Best accuracy-to-complexity ratio for tabular data. No GPU required. Built-in feature importances. scikit-learn has zero extra infrastructure.
**Tradeoffs**: Slightly slower training than Random Forest, but inference is fast. Less powerful than XGBoost but avoids extra dependency.
**Consequences**: Model ships as <1MB joblib file. Prediction takes <1ms.

---

## D002: ML Role — Advisory vs Authority
**Problem**: Should the ML model's prediction be the final triage level?
**Alternatives**:
1. ML is the final authority
2. ML is advisory-only — deterministic rules form a safety floor
3. ML and rules are equal — disagreements require clinician resolution

**Choice**: Advisory-only with rules floor
**Rationale**: The Accenture brief explicitly says "any recommendation must remain reviewable and overridable." Under-triage is catastrophically worse than over-triage. A rules floor guarantees no critical case is missed even if the model fails.
**Tradeoffs**: ML can never downgrade a patient, which means some over-triage. This is acceptable per the brief's explicit requirement.
**Consequences**: Reconciler enforces `final_level = min(rules_level_num, ml_level_num)` (lower number = higher severity). Disagreements are logged and shown.

---

## D003: Age Stratification Approach
**Problem**: Vital sign thresholds differ across age populations.
**Alternatives**:
1. Separate threshold tables per age group (pediatric/adult/geriatric)
2. Single model with age as a continuous weight multiplier
3. Separate models per age group

**Choice**: Separate threshold tables per age group
**Rationale**: Clinical practice uses distinct normal ranges per population. A table-based approach is transparent, auditable, and matches how triage nurses actually think. A continuous multiplier obscures the clinical basis.
**Tradeoffs**: Three code paths vs one. More maintenance but much more clinically defensible.
**Consequences**: Rules engine selects threshold table based on `age_group` before evaluation.

---

## D004: Training Data Strategy
**Problem**: No real patient data available for ML training.
**Alternatives**:
1. Synthetic data generated from clinical rules + controlled noise
2. MIMIC-III/IV public dataset
3. No ML (rules only)

**Choice**: Synthetic data from clinical rules
**Rationale**: MIMIC requires data use agreements and complex ETL. Synthetic data is controllable, reproducible, and demonstrates the full ML pipeline. The model architecture is designed to swap to real data without changes.
**Tradeoffs**: Model quality is limited by how realistic the synthetic data is. Explicitly documented as a prototype limitation.
**Consequences**: Training pipeline generates ~2000 records covering all age groups, complaint categories, and edge cases.

---

## D005: Frontend Technology
**Problem**: Should we upgrade the frontend for Stage 2?
**Alternatives**:
1. Keep Vanilla JS (extend what exists)
2. Migrate to React
3. Migrate to Vue

**Choice**: Keep Vanilla JS
**Rationale**: Stage 1 deliberately chose vanilla JS. The brief doesn't require a framework. Migration would consume time better spent on ML and simulation. The UI requirements (forms, cards, stats) are achievable in vanilla JS.
**Tradeoffs**: More manual DOM manipulation. No component reuse. Acceptable for prototype scale.
**Consequences**: Extend existing app.js, index.html, style.css. No new build tooling.

---

## D006: Storage for Stage 2
**Problem**: Should we add database persistence?
**Alternatives**:
1. Keep in-memory (same as Stage 1)
2. Add SQLite
3. Add Redis

**Choice**: Keep in-memory
**Rationale**: The brief says "simulated patient data." Persistence adds complexity without advancing the core triage demonstration. Documented as Stage 3 improvement.
**Tradeoffs**: State lost on restart. Acceptable for prototype.
**Consequences**: Queue, audit logs, ML predictions all in-memory. No migration scripts needed.

---

## D007: Surge Simulation Strategy
**Problem**: Stage 1 surge just loads 20 fixed patients. Brief requires realistic 3× volume.
**Alternatives**:
1. Generate 60 new random patients (3× the base 20)
2. Multiply the 20 seed patients with variations
3. Time-based arrival simulation

**Choice**: Generate 60 new random patients from clinical archetypes
**Rationale**: Demonstrates scalability and data diversity. Random generation shows the system handles novel patients, not just memorized seed data.
**Tradeoffs**: Random patients may be less clinically realistic than hand-crafted ones. Mitigated by using archetype templates.
**Consequences**: Patient generator uses 8 clinical archetypes (chest pain, respiratory, trauma, pediatric fever, geriatric fall, abdominal, neurological, minor injury) with controlled randomization.

---

## D008: Deterioration Simulation
**Problem**: How to simulate patients worsening while waiting.
**Alternatives**:
1. Server-side random deterioration on API call (manual trigger)
2. Background asyncio task (automatic)
3. Client-side polling with server mutation

**Choice**: Server-side on API call (manual trigger from UI)
**Rationale**: Background tasks in FastAPI require careful lifecycle management. A manual trigger is simpler, reproducible, and lets the evaluator control when deterioration happens.
**Tradeoffs**: Not automatic — evaluator must click a button. But this is more demo-friendly.
**Consequences**: `POST /api/simulate/deteriorate` endpoint. Frontend has a "Simulate Deterioration" button.

---

## D009: Reconciler Disagreement Handling
**Problem**: What happens when ML and rules disagree?
**Alternatives**:
1. Always take the more severe (our choice)
2. Average the two scores
3. Flag for mandatory clinician review

**Choice**: Always take the more severe
**Rationale**: The brief explicitly says "bias toward escalation under uncertainty." Taking the more severe option of the two is the safest approach and directly satisfies this requirement.
**Tradeoffs**: Over-triage risk. Acceptable — the brief says "missing a critical case is categorically worse."
**Consequences**: `final_level = min(rules_level_num, ml_level_num)`. Disagreement logged in audit.
