# System Architecture & Data Pipeline

This section outlines the end-to-end data flow for the Patient Triage AI, demonstrating how patient information is ingested, processed, and presented to healthcare professionals.

## Architecture Diagram

```text
+---------------------------------------------------------+
|                  1. DATA INGESTION                      |
+---------------------------------------------------------+
       |                                      |
 [ Patient Mobile App ]              [ Hospital EHR System ]
 (Natural Language Symptoms)         (Patient History/Vitals)
       |                                      |
       +------------------+-------------------+
                          |
                          v
+---------------------------------------------------------+
|              2. AI PROCESSING PIPELINE                  |
+---------------------------------------------------------+
                          |
               [ Secure API Gateway ]
                          |
                          v
          [ Security & Anonymization Layer ]
               (Encrypts & Masks PHI)
                          |
                          v
            [ NLP Symptom Extraction Module ]
              (Identifies Medical Entities)
                          |
                          v
             [ ML Severity Risk Scoring ]
             (Generates Acuity Prediction)
                          |
                          v
            [ Clinical Rules & Guardrails ]
           (Catches Critical Red-Flag Cases)
                          |
                          v
+---------------------------------------------------------+
|              3. OUTPUT & WORKFLOW                       |
+---------------------------------------------------------+
                          |
             [ Triage Nurse Dashboard ]
        (Displays AI Summary & Priority Queue)
                          |
                          v
           [ Human-in-the-Loop Validation ]
      (Nurse Confirms or Overrides AI Decision)
                          |
        +-----------------+-----------------+
        |                                   |
        v                                   | (Continuous
[ Write Final Decision ]                    |  Learning Loop)
[ to Hospital EHR      ]--------------------+
```


## Data Pipeline Flow Explanation

1. **Data Ingestion (Input):** 
   Information enters the system through two main channels: 
   * Active input from the patient using natural language via a mobile app or hospital kiosk.
   * Passive data retrieval, securely pulling the patient’s historical medical data and recent vitals directly from the hospital's EHR system using standardized FHIR/HL7 protocols.

2. **AI Processing Pipeline (The Core):** 
   * **Security:** All incoming data first passes through a security gateway where Protected Health Information (PHI) is encrypted and temporarily anonymized for processing.
   * **NLP Extraction:** The Natural Language Processing module breaks down the patient's text, identifying key medical entities (e.g., extracting "severe chest pressure" and "radiating arm pain").
   * **Risk Scoring:** The Machine Learning engine analyzes the extracted entities against historical data to generate a preliminary acuity score.
   * **Clinical Guardrails:** Before any score is outputted, a hardcoded rules engine ensures critical red-flag symptoms (like signs of a stroke or heart attack) automatically trigger maximum priority overrides, regardless of the ML score.

3. **Output & Clinical Workflow (Action):**
   * The analyzed data is securely logged and immediately surfaced on the **Triage Nurse Dashboard**. 
   * The dashboard highlights the AI’s recommended triage level alongside a clear summary of extracted symptoms ("Explainable AI").
   * **Human-in-the-Loop:** The triage nurse reviews the AI's recommendation and confirms or overrides the final triage level.
   * The final decision is seamlessly written back to the hospital's EHR system, and any overrides are fed back into the AI loop to continuously improve the model's future accuracy.
