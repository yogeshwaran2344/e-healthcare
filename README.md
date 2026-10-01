 AI Personal Health Navigator & Multimodal Clinical Handover System

An advanced, adaptive healthcare system that transforms traditional static symptom checkers into an **Adaptive Multimodal AI Health Triage, Automated Lab Biomarker Extraction, SBAR Clinical Handover, and Longitudinal Recovery Monitoring System**.

---

 Key Innovations & Architecture

```
                 USER
                   ↓
         [Text / Voice / Scans]
                   ↓
        ┌─────────────────────┐
        │ Patient Context     │
        │ • Age & Gender      │
        │ • Chronic Illnesses │
        │ • Regular Meds      │
        │ • Drug Allergies    │
        └──────────┬──────────┘
                   ↓
      Adaptive Clinical Questions (Dynamic Follow-up)
                   ↓
        Multimodal AI Engine
        ↙          ↓          ↘
    Symptoms    Lab Scans    Medical History
        ↘          ↓          ↙
       3-Tier Risk Triage & Explainable AI (XAI)
                   ↓
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    Self-Care    Doctor    Emergency
                 Consult
                   ↓
          AI Clinical Handover (SBAR)
                   ↓
        Attending Physician Review
                   ↓
     Medication Safety & Drug Allergy Check
                   ↓
         Digital Verified Prescription
                   ↓
     Longitudinal Recovery Feedback Loop (Day 1, 3, 7)
                   ↺
```

---

##  Features Implemented

### 1 Multi-Stage Adaptive AI Clinical Assessment
- **Stage 1: Symptom Intake**: Text keyword search, multi-system symptom chips, or direct Voice input.
- **Stage 2: Dynamic Targeted Questions**: Generates 3-5 clinical follow-up questions tailored to observed symptoms (e.g. onset days, pain scale 1-10, measured fever temperature, phlegm character, prior OTC medications taken).
- **Stage 3: Contextual Bayesian Diagnostic Classifier**: Synthesizes symptoms + individual patient baseline (age, pre-existing Diabetes / Hypertension).
- **Stage 4: Explainable AI (XAI)**: Explicitly explains *why* each condition was considered (e.g. matched core symptoms, biomarker elevation, patient chronic history modifier).

### 2. Medical Report Understanding & Biomarker Extraction
- Upload lab tests (Blood CBC, Liver LFT, Kidney KFT) and scans (Chest X-Ray, CT Scan).
- Automatically parses parameters (Platelet count, WBC / TLC, Hemoglobin, Bilirubin, Fasting Blood Sugar) and detects radiology findings (consolidation, infiltrate, cardiomegaly).
- Flags out-of-range biomarkers (e.g. *Low Platelets: 68,000 /µL - Thrombocytopenia*) and feeds findings directly into the AI diagnosis.

### 3.  3-Tier Risk & Urgency Engine (Triage)
- ** Self-Care / Home Monitoring**: Mild self-limiting symptoms with lifestyle care guidance.
- ** Doctor Consultation Recommended**: Persistent infection or abnormal biomarkers requiring clinical evaluation.
- ** Emergency Care**: Detects critical red flags (chest pain radiating, severe dyspnea, extreme pain 9-10/10, platelet crash) and triggers urgent hospital ER directions.

### 4. Voice-Based Consultation (Speech-to-Text)
- Integrated microphone button powered by the Web Speech API.
- Supports **English (India)**, **Hindi (हिन्दी)**, and **Kannada (ಕನ್ನಡ)**.
- Spoken speech is transcribed and automatically highlighted as corresponding symptoms.

### 5. AI → Doctor Clinical Handover (SBAR Format)
- Produces a structured, clinical-grade **SBAR** handover for the physician before consultation begins:
  - **[S] Situation**: Chief complaints, quantified duration, pain scale (1-10).
  - **[B] Background**: Demographics, pre-existing chronic conditions, regular medications, and known drug allergies.
  - **[A] Assessment**: AI Triage Urgency, suspected etiology, extracted abnormal lab biomarkers.
  - **[R] Recommendation**: Suggested clinical inquiries and examination considerations.
- Eliminates repetitive questioning and significantly reduces doctor intake time.

### 6.  Medication Safety & Drug Allergy Checker
- Real-time safety engine cross-references prescribed medicines against the patient's declared allergies and conditions.
- **Live Allergy Alert**: E.g., if a doctor prescribes *Amoxicillin* to a patient with a documented *Penicillin* allergy, the system immediately flashes a critical allergy warning.
- Warns against disease contraindications (e.g., NSAIDs in Gastric Ulcer/Asthma).

### 7.  Personal Health Profile (Longitudinal Context)
- Stores age, gender, blood group, chronic conditions, current medications, and known drug allergies.

### 8.  Continuous Post-Consultation Recovery Monitoring (Feedback Loop)
- Patients log recovery check-ins at Day 1, Day 3, and Day 7 (temperature, symptom progression, notes).
- AI evaluates trajectory and provides continuous feedback (Recovery on track vs. Re-consultation warning).


### 1. I + Predictive Care & Deterioration Forecaster
- **Deterioration Risk Index (0-100)**: Multi-factorial probabilistic algorithm that evaluates Bayesian symptom progression, live IoT vital trends, lab biomarker deviations, and chronic baselines.
- **Predictive Scheduling Engine**: Computes optimal clinical follow-up horizons (`Within 24-48 hours`, `Within 3-5 days`, or `Routine 10-14 days`) and proactively suggests appointment slots with matching specialists *before* exacerbations turn critical.
- **Chronic Condition Alert Shield**: Autonomous real-time surveillance for diabetic glycemic spikes, hypertensive crisis trends, and drug-allergy contraindication barriers.

### 2 IoT Medical Wearables Integration & Telemetry Stream
- **Wearable Sensor Aggregator**: Pairs with Omron BP monitors, Dexcom Continuous Glucose Monitors (CGM), KardiaMobile ECG patches, and Wellue SpO2 rings.
- **Real-Time Synchronized Telemetry**: Live biometric feeds streamed directly into patient and clinician dashboards with dynamic canvas Lead-II ECG waveform visualization.
- **Critical Threshold Edge Alert Engine**: Triggers instant audio-visual alarms when vitals cross clinical danger boundaries (SpO2 < 90%, BP > 180/120, HR > 140 bpm, Glucose > 300 mg/dL) with auto-prompting for emergency hospital dispatch.

### 3. Patient-Owned Blockchain Health Ledger & Smart Consent Matrix
- **Tamper-Evident SHA-256 Block Chain**: Every consultation, diagnosis, lab finding, and prescription is cryptographically hashed and linked into an immutable Merkle tree ledger.
- **Proof-of-Integrity Mathematical Verifier**: One-click traversal and re-computation of block headers from the Genesis Anchor to current tip, guaranteeing zero data tampering.
- **Decentralized Smart Consent Matrix**: Patients retain sovereign ownership and grant time-bounded, cryptographically signed access tokens with granular permission scopes (`diagnoses`, `lab_reports`, `prescriptions`, `live_vitals`) to doctors, insurers, and researchers with instant revocation logging.

### 4. Smart Indoor AR Hospital Navigation & Priority Queue
- **Multi-Floor Topological Navigation Graph**: Shortest-path indoor routing using Dijkstra's algorithm across Ground, 1st, and 2nd hospital floors.
- **Augmented Reality (AR) Camera HUD**: Real-time simulated camera viewfinder overlay with waypoint guidance, heading bearing, distance meters, and directional arrows.
- **Clinical Urgency Dynamic Queue**: Real-time token tracking (`A-114`, `Serving: A-112`, dynamic wait time calculation). Patients tagged with Emergency Care or critical IoT alerts are automatically elevated to **Priority P0 Emergency Bypass** at the head of the queue.

### 5. Rapid Emergency SOS & Live GPS Ambulance Tracking
- **1-Tap Autonomous SOS Dispatcher**: Generates an instant digital **Emergency Medical Passport** (Blood Group, Critical Allergies, Chronic Conditions, Current Meds, Live IoT Vitals) and transmits it to the receiving ER trauma team.
- **Dynamic GPS Ambulance Telemetry HUD**: Real-time tracking of dispatched Advanced Life Support (ALS) cardiac units with traffic-optimized ETA decay, paramedic communication, and siren status.
- **Pre-Hospital Trauma Orchestration**: Automatically reserves hospital ER Trauma Bay beds and pre-stages blood bank cross-matches prior to ambulance hospital arrival.

### 6. Community Support Circles & Gamified Preventive Health
- **AI Clinical Misinformation & Safety Moderation**: Real-time NLP filter scanning patient peer posts for dangerous medical claims, unverified home cures, and toxicity, awarding an "AI Verified Safe" badge to sound peer advice.
- **Gamified Wellness Adherence Engine**: Daily 10,000 steps, 2.5L hydration, 7-day blood pressure logging streak, and sugar-free challenges with streak tracking and point multipliers.
- **Patient Loyalty Points & Health Badges**: Rewards catalog (`Gold Vitality`, badges: `Hydration Hero`, `Glucose Guardian`, `Blockchain Sovereign`) redeemable for lab test vouchers.
- **Chronic-Tailored AI Lifestyle Coach**: Synthesizes condition-specific nutrition (e.g., Low GI Mediterranean for diabetics, DASH sodium-restriction for hypertension), targeted exercise regimens, and vagus nerve breathing exercises.
