# PatientTriage.ai - Alignment with Accenture Brief

Based on the Accenture Prototype Development brief for Problem Track 2, here is an analysis of the current project state, the features that still need to be added, and pipeline improvements to meet the enterprise-level expectations.

## 1. Introducing a Unified Patient Severity Score (The "Why")

Currently, the queue sorts patients based strictly on their priority category (LEVEL 1-5) and then by their wait time. This misses the nuanced, continuous risk assessment requested in the brief. 

To fix this, we need to introduce a **0-100 Patient Severity Score (or Risk Index)**.
- **Why it's needed:** A severity score allows us to rank patients *within* the same triage level. If two patients are both LEVEL 2, the one with a score of 88 should be seen before the one with a score of 74, even if they arrived a few minutes later. 
- **How it works:** The score combines the deterministic rules output, the ML probability, and demographic risk factors (like age) into a single integer.
- **Explainability:** In the queue, next to the score, we can show exactly *why* they are at the top. For example: `Score: 85 (Base Risk: 60 + Geriatric Adjustment: +15 + Elevated Heart Rate: +10)`. This provides the instant explainability required for clinicians making decisions in seconds.

## 2. Pipeline Improvements at Every Step

**Step 1: Data Ingestion & Strategy**
- **Current State:** The system accepts basic vital signs and flags if medical history is available.
- **Improvement:** Implement a "Data Completeness Penalty." The brief emphasizes that returning patients have rich histories while first-timers have none. If critical data is missing, the pipeline should explicitly lower the "Confidence" metric and bias the severity score toward caution (escalation). 

**Step 2: Decision Modeling (The Triage Engine)**
- **Current State:** Hardcoded rules and an ML predictor running in parallel, with a reconciler.
- **Improvement:** The rules engine must be strictly calibrated by age group. A fever of 38.5°C means something entirely different for a 3-year-old versus a 75-year-old. The pipeline needs branching logic (Pediatric, Adult, Geriatric) before calculating the baseline risk. Additionally, the ML model should output a formal uncertainty metric (not just confidence), ensuring the system explicitly communicates when it is "unsure" about a patient.

**Step 3: Queue Management & Deterioration (Safety-First)**
- **Current State:** Patients are flagged if they wait too long or if updated vitals cross hard thresholds (e.g., HR > 120).
- **Improvement:** Move from static threshold checks to dynamic velocity checks. If a patient's Severity Score increases by more than 10 points between vitals checks, the system should trigger an immediate "Deterioration Alert," overriding standard wait times. Surge mode should also dynamically shrink the reassessment windows based on the current staff-to-patient ratio.

**Step 4: Audit & Re-training (Governance)**
- **Current State:** Basic audit logging of triage events and overrides.
- **Improvement:** Enhance the feedback loop. When a clinician overrides a decision, the UI must capture structured reasons (e.g., "Patient appears toxic despite normal vitals") rather than just free text. Ensure that the logs are sanitized (PII stripped) to demonstrate HIPAA/GDPR compliance before being used to re-train the ML model.

## 3. Features Still Needed for the Final Prototype

To fully meet the "Working Prototype" expectations laid out in the brief, the following features must be added:

1. **Explicit Uncertainty Surfacing:** The UI must visually block or caution a triage score if the system's confidence falls below a certain threshold. The brief explicitly states: *"the prototype must not return a score without a confidence indicator."*
2. **Hospital-Specific Configuration Layer (Scalability):** A configuration file or admin settings page that allows a hospital to tune the system for their specific context (e.g., rural clinic vs. urban trauma center). This proves the solution can generalize.
3. **Age-Specific Test Cases:** We need to simulate specific patient records for ambiguous presentations, pediatric/geriatric cases, and zero-history patients to demonstrate how the scoring logic adapts to these edge cases.
4. **Surge UI/UX Adapters:** When a surge is simulated (3x volume), the frontend should subtly adapt—perhaps collapsing less critical information to reduce cognitive load on the nurse and highlighting only the most critical, escalating patients.
5. **Data Protection / Privacy Mode:** A toggle or automated timeout that masks patient PII (Names, DOBs) on the nurse's dashboard to prevent unauthorized viewing, addressing the patient data protection requirements.

---

# Architectural Discussion: Session-Based Storage & Supabase Integration

Your idea of moving to a persistent, session-based storage system (like Supabase/PostgreSQL) is a massive leap forward in making this application robust, scalable, and enterprise-ready. 

Currently, the application relies on an ephemeral, in-memory Python dictionary (`queue_manager.queue`). If the Python server restarts, all data is lost. Shifting to an external database completely changes how we handle roles, data security, and real-time updates.

Here is a breakdown of how we can design this architecture:

## 1. The "Session" Lifecycle Management
Since this application acts as a dynamic triage simulator/tool, treating the queues as "Sessions" or "Shifts" is a perfect abstraction.

*   **Session Creation:** When the application starts, we create a new record in a `sessions` table (e.g., `session_id: uuid, status: 'active', created_at: timestamp`).
*   **Data Tagging:** Every patient, triage event, and override generated during this time is tagged with this `session_id` in the database.
*   **Session Closure:** When the user clicks "End Session" or "Clear All", we don't permanently delete the data. Instead, we update the session status to `closed`. 
*   **New Session:** A new `session_id` is generated. Because the frontend is querying `WHERE session_id = <active_session>`, the board instantly clears, starting fresh while preserving historical data for later analytics.

## 2. Solving Role-Based Access natively (The Supabase Advantage)
Your suggestion to handle role-based loading directly at the storage level is exactly how modern secure applications operate. Supabase (which is built on PostgreSQL) offers **Row-Level Security (RLS)** and **Column-Level Privileges**.

Instead of writing Python logic to manually "scrub" vitals from the JSON payload (our current plan), we let the database handle security natively:
*   **Database Roles:** We create distinct database roles for `clinician` and `receptionist`.
*   **Column-Level Security:** We grant the `receptionist` role permission to `SELECT` the `name`, `id`, `wait_time`, and `priority` columns from the `patients` table. We completely *deny* them permission to `SELECT` the `vitals` or `ml_confidence` columns.
*   **The Result:** When the frontend requests data as a Receptionist, the database physically refuses to return the clinical columns. The backend doesn't have to do any manual scrubbing, making data leaks practically impossible. When you switch back to Clinician, the database allows full access again.

## 3. Upgrading to Real-Time WebSockets
Currently, your frontend (`app.js`) uses "polling" to fetch data (pinging the server every 3 seconds).
If we move to Supabase, we can utilize their **Realtime** subscriptions. The frontend can open a direct WebSocket connection to the database:
*   Instead of repeatedly asking the server if there is new data, the database *pushes* changes to the frontend the millisecond a patient's vitals deteriorate or a new walk-in arrives.
*   These real-time subscriptions inherently respect the Role-Based Access policies discussed above.

## 4. Implementation Phasing (High-Level Plan)

If we decide to go down this route, here is how we would phase the migration without breaking the current app:

*   **Phase 1: Database Provisioning:** Spin up a Supabase project and design the schema (`sessions`, `patients`, `audit_logs`). Configure the RLS policies for Clinician vs. Receptionist.
*   **Phase 2: Backend Refactor (The Storage Adapter):** Modify `queue_monitor.py`. Instead of writing to a local Python dictionary, `QueueMonitor` will use the Supabase Python Client to `INSERT` and `UPDATE` records in the database.
*   **Phase 3: Frontend Refactor:** Update `app.js` to handle session IDs and fetch data based on the active session, eventually swapping out the 3-second polling for a Supabase Realtime listener.

### Discussion Point
Moving to Supabase takes us from a "prototype" to a "production-ready architecture." It solves the data leak problem elegantly at the database layer and enables historical session tracking. 
