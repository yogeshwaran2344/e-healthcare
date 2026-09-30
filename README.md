# 🩺 AI Personal Health Navigator & Multimodal Clinical Handover System

An advanced, adaptive healthcare system that transforms traditional static symptom checkers into an **Adaptive Multimodal AI Health Triage, Automated Lab Biomarker Extraction, SBAR Clinical Handover, and Longitudinal Recovery Monitoring System**.

---

## 🚀 Key Innovations & Architecture

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

## ✨ Features Implemented

### 1. 🧠 Multi-Stage Adaptive AI Clinical Assessment
- **Stage 1: Symptom Intake**: Text keyword search, multi-system symptom chips, or direct Voice input.
- **Stage 2: Dynamic Targeted Questions**: Generates 3-5 clinical follow-up questions tailored to observed symptoms (e.g. onset days, pain scale 1-10, measured fever temperature, phlegm character, prior OTC medications taken).
- **Stage 3: Contextual Bayesian Diagnostic Classifier**: Synthesizes symptoms + individual patient baseline (age, pre-existing Diabetes / Hypertension).
- **Stage 4: Explainable AI (XAI)**: Explicitly explains *why* each condition was considered (e.g. matched core symptoms, biomarker elevation, patient chronic history modifier).

### 2. 📸 Medical Report Understanding & Biomarker Extraction
- Upload lab tests (Blood CBC, Liver LFT, Kidney KFT) and scans (Chest X-Ray, CT Scan).
- Automatically parses parameters (Platelet count, WBC / TLC, Hemoglobin, Bilirubin, Fasting Blood Sugar) and detects radiology findings (consolidation, infiltrate, cardiomegaly).
- Flags out-of-range biomarkers (e.g. *Low Platelets: 68,000 /µL - Thrombocytopenia*) and feeds findings directly into the AI diagnosis.

### 3. 🚨 3-Tier Risk & Urgency Engine (Triage)
- **🟢 Self-Care / Home Monitoring**: Mild self-limiting symptoms with lifestyle care guidance.
- **🟡 Doctor Consultation Recommended**: Persistent infection or abnormal biomarkers requiring clinical evaluation.
- **🔴 Emergency Care**: Detects critical red flags (chest pain radiating, severe dyspnea, extreme pain 9-10/10, platelet crash) and triggers urgent hospital ER directions.

### 4. 🗣️ Voice-Based Consultation (Speech-to-Text)
- Integrated microphone button powered by the Web Speech API.
- Supports **English (India)**, **Hindi (हिन्दी)**, and **Kannada (ಕನ್ನಡ)**.
- Spoken speech is transcribed and automatically highlighted as corresponding symptoms.

### 5. 🧑‍⚕️ AI → Doctor Clinical Handover (SBAR Format)
- Produces a structured, clinical-grade **SBAR** handover for the physician before consultation begins:
  - **[S] Situation**: Chief complaints, quantified duration, pain scale (1-10).
  - **[B] Background**: Demographics, pre-existing chronic conditions, regular medications, and known drug allergies.
  - **[A] Assessment**: AI Triage Urgency, suspected etiology, extracted abnormal lab biomarkers.
  - **[R] Recommendation**: Suggested clinical inquiries and examination considerations.
- Eliminates repetitive questioning and significantly reduces doctor intake time.

### 6. 💊 Medication Safety & Drug Allergy Checker
- Real-time safety engine cross-references prescribed medicines against the patient's declared allergies and conditions.
- **Live Allergy Alert**: E.g., if a doctor prescribes *Amoxicillin* to a patient with a documented *Penicillin* allergy, the system immediately flashes a critical allergy warning.
- Warns against disease contraindications (e.g., NSAIDs in Gastric Ulcer/Asthma).

### 7. 📊 Personal Health Profile (Longitudinal Context)
- Stores age, gender, blood group, chronic conditions, current medications, and known drug allergies.

### 8. 🔄 Continuous Post-Consultation Recovery Monitoring (Feedback Loop)
- Patients log recovery check-ins at Day 1, Day 3, and Day 7 (temperature, symptom progression, notes).
- AI evaluates trajectory and provides continuous feedback (Recovery on track vs. Re-consultation warning).

---

## ⚖️ Novel Patentable Healthcare Architecture & Add-Ons (v3.0)

Layered directly on top of the clinical base system, the platform incorporates **6 novel patentable systems**:

### 1. 🧠 AI + Predictive Care & Deterioration Forecaster
- **Deterioration Risk Index (0-100)**: Multi-factorial probabilistic algorithm that evaluates Bayesian symptom progression, live IoT vital trends, lab biomarker deviations, and chronic baselines.
- **Predictive Scheduling Engine**: Computes optimal clinical follow-up horizons (`Within 24-48 hours`, `Within 3-5 days`, or `Routine 10-14 days`) and proactively suggests appointment slots with matching specialists *before* exacerbations turn critical.
- **Chronic Condition Alert Shield**: Autonomous real-time surveillance for diabetic glycemic spikes, hypertensive crisis trends, and drug-allergy contraindication barriers.

### 2. ⌚ IoT Medical Wearables Integration & Telemetry Stream
- **Wearable Sensor Aggregator**: Pairs with Omron BP monitors, Dexcom Continuous Glucose Monitors (CGM), KardiaMobile ECG patches, and Wellue SpO2 rings.
- **Real-Time Synchronized Telemetry**: Live biometric feeds streamed directly into patient and clinician dashboards with dynamic canvas Lead-II ECG waveform visualization.
- **Critical Threshold Edge Alert Engine**: Triggers instant audio-visual alarms when vitals cross clinical danger boundaries (SpO2 < 90%, BP > 180/120, HR > 140 bpm, Glucose > 300 mg/dL) with auto-prompting for emergency hospital dispatch.

### 3. ⛓️ Patient-Owned Blockchain Health Ledger & Smart Consent Matrix
- **Tamper-Evident SHA-256 Block Chain**: Every consultation, diagnosis, lab finding, and prescription is cryptographically hashed and linked into an immutable Merkle tree ledger.
- **Proof-of-Integrity Mathematical Verifier**: One-click traversal and re-computation of block headers from the Genesis Anchor to current tip, guaranteeing zero data tampering.
- **Decentralized Smart Consent Matrix**: Patients retain sovereign ownership and grant time-bounded, cryptographically signed access tokens with granular permission scopes (`diagnoses`, `lab_reports`, `prescriptions`, `live_vitals`) to doctors, insurers, and researchers with instant revocation logging.

### 4. 🗺️ Smart Indoor AR Hospital Navigation & Priority Queue
- **Multi-Floor Topological Navigation Graph**: Shortest-path indoor routing using Dijkstra's algorithm across Ground, 1st, and 2nd hospital floors.
- **Augmented Reality (AR) Camera HUD**: Real-time simulated camera viewfinder overlay with waypoint guidance, heading bearing, distance meters, and directional arrows.
- **Clinical Urgency Dynamic Queue**: Real-time token tracking (`A-114`, `Serving: A-112`, dynamic wait time calculation). Patients tagged with Emergency Care or critical IoT alerts are automatically elevated to **Priority P0 Emergency Bypass** at the head of the queue.

### 5. 🚨 Rapid Emergency SOS & Live GPS Ambulance Tracking
- **1-Tap Autonomous SOS Dispatcher**: Generates an instant digital **Emergency Medical Passport** (Blood Group, Critical Allergies, Chronic Conditions, Current Meds, Live IoT Vitals) and transmits it to the receiving ER trauma team.
- **Dynamic GPS Ambulance Telemetry HUD**: Real-time tracking of dispatched Advanced Life Support (ALS) cardiac units with traffic-optimized ETA decay, paramedic communication, and siren status.
- **Pre-Hospital Trauma Orchestration**: Automatically reserves hospital ER Trauma Bay beds and pre-stages blood bank cross-matches prior to ambulance hospital arrival.

### 6. 👥 Community Support Circles & Gamified Preventive Health
- **AI Clinical Misinformation & Safety Moderation**: Real-time NLP filter scanning patient peer posts for dangerous medical claims, unverified home cures, and toxicity, awarding an "AI Verified Safe" badge to sound peer advice.
- **Gamified Wellness Adherence Engine**: Daily 10,000 steps, 2.5L hydration, 7-day blood pressure logging streak, and sugar-free challenges with streak tracking and point multipliers.
- **Patient Loyalty Points & Health Badges**: Rewards catalog (`Gold Vitality`, badges: `Hydration Hero`, `Glucose Guardian`, `Blockchain Sovereign`) redeemable for lab test vouchers.
- **Chronic-Tailored AI Lifestyle Coach**: Synthesizes condition-specific nutrition (e.g., Low GI Mediterranean for diabetics, DASH sodium-restriction for hypertension), targeted exercise regimens, and vagus nerve breathing exercises.

---

## ⚖️ Patentability Strategy & Claims Mapping

| Patent Dimension | Novel Method / Workflow Implemented in Code |
| :--- | :--- |
| **Novelty** | Synergy across heterogeneous systems: Edge IoT telemetry trigger $\rightarrow$ Autonomous Emergency Medical Passport generation $\rightarrow$ Blockchain Merkle ledger immutability $\rightarrow$ AR indoor navigation waypoint projection. |
| **Technical Implementation** | Discrete algorithmic engines: Dijkstra indoor path solver, SHA-256 Merkle chain verification, Bayesian deterioration risk index, dynamic priority queue insertion, and NLP clinical misinformation filter. |
| **Utility** | Eliminates OPD waiting confusion, prevents chronic condition emergencies, terminates clinical medical record tampering, and slashes ambulance pre-hospital handover latency. |
| **Step-by-Step Workflow** | Detailed state transitions from sensor ingest $\rightarrow$ threshold breach $\rightarrow$ blockchain event $\rightarrow$ priority queue promotion $\rightarrow$ clinician SBAR handover. |

---

## 🏃 Quick Start Guide

### 1. Open in Visual Studio Code
- Open **VS Code** $\rightarrow$ **File** $\rightarrow$ **Open Folder...** $\rightarrow$ `C:\Users\yoges\Downloads\e-healthcare`

### 2. Run the Server
Open the integrated terminal (`Ctrl + ~`) and run:
```bash
.\run.bat
```
*(Or run `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`)*

### 3. Open in Browser
- **Web App**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Explorer**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 👤 Pre-configured Demo Accounts

| Role | Email | Password | Pre-configured Profile / Details |
| :--- | :--- | :--- | :--- |
| **Doctor** | `doctor@example.com` | `doctor123` | **Dr. Sarah Sharma** (Pulmonologist & Critical Care) |
| **Patient** | `patient@example.com` | `patient123` | **Rahul Verma** (Age 48, Male, Diabetes Type 2, **Allergic to Penicillin**) |

---

## 🧪 Comprehensive Presentation Demo Script

### Demo 1: AI Predictive Care & Chronic Alerts
1. Log in as **Rahul Verma** (`patient@example.com` / `patient123`).
2. Click **1. AI Predictive Care** tab:
   - View the **Deterioration Risk Index (63% - Moderate Risk)** and clinical factors.
   - Inspect the **Predictive Follow-Up Suggestion** with suggested specialist and date.
   - Click **Confirm & Reserve Proactive Slot** to confirm the appointment.
   - Inspect active **Chronic Alerts** (Hyperglycemia vigilance, Hypertension warning, Penicillin allergy shield).

### Demo 2: IoT Wearables & Live Vitals
1. Click **2. IoT Wearables** tab:
   - Observe paired medical devices (Omron BP, Dexcom CGM, Kardia ECG, Wellue SpO2).
   - View live telemetry metric cards and the animated green Lead-II ECG rhythm waveform.
   - Click **Simulate Critical SpO2 Breach (87%)**: Watch the system flash a real-time **Critical Vital Threshold Breach Banner** with immediate 1-tap SOS dispatch!

### Demo 3: Blockchain Health Records & Smart Consent
1. Click **3. Blockchain Records** tab:
   - Inspect the cryptographic SHA-256 block ledger (Block #0 Genesis, Block #1 Consultation).
   - Click **Verify Ledger Cryptographic Integrity**: Watch the mathematical proof run and stamp **100% Intact Zero Tampering**.
   - Inspect the **Smart Consent Matrix** showing active permissions granted to Dr. Sarah Sharma.
   - Click **+ Grant New Smart Consent** to issue a granular, time-bound sharing token to an insurance auditor.

### Demo 4: Indoor AR Navigation & Smart Queue
1. Click **4. Indoor AR Nav & Queue** tab:
   - Switch between **Ground Floor**, **1st Floor (OPD)**, and **2nd Floor (Diagnostics)**.
   - Select destination **Dr. Sarah Sharma (Suite 104 - Pulmonology)**: Watch the interactive SVG map draw the optimal red dashed route line and list turn-by-turn steps.
   - Click **Open AR Camera HUD** to see the augmented reality heads-up display overlay.
   - View your **Live OPD Queue Ticket (A-114)** with current serving number and wait time.

### Demo 5: 1-Tap Rapid SOS Emergency & Live Ambulance
1. Click the pulsating **🚨 1-Tap SOS Emergency** button in the navbar:
   - Watch the system trigger the rapid dispatch of ALS-Unit 07 (Cardiac Life Support).
   - View live GPS ambulance telemetry tracking moving toward the patient with real-time ETA decay.
   - Inspect the auto-generated **Emergency Medical Passport** (Blood Group B+, Penicillin Allergy, Vitals) pre-transmitted to Trauma Bay #3.

### Demo 6: Community & Preventive Health
1. Click **6. Community & Wellness** tab:
   - View AI-moderated peer posts with the **AI Verified Safe** badge.
   - In the post composer, submit a supportive diet or exercise tip: Watch the AI safety filter verify and approve the post.
   - View your **Preventive Health Challenges** (10k steps, 2.5L hydration, 7-day BP streak) and click **+ Log** to earn reward points.
   - Inspect the **AI Chronic Lifestyle Coach** with custom nutrition and exercise advice tailored to Type 2 Diabetes and Hypertension.

### Demo 7: Clinician View (Doctor Portal)
1. Log in as **Dr. Sarah Sharma** (`doctor@example.com` / `doctor123`).
2. Switch tabs:
   - **IoT Telemetry & RPM Monitor**: View live vitals and Lead-II ECG of assigned patients.
   - **Inbound ER Board**: View approaching ambulances, ETAs, and reserved trauma bay beds.
   - **OPD Queue Console**: Call waiting patients or execute an **Emergency P0 Priority Bump**.
   - **Blockchain Audit Verifier**: Cryptographically verify the patient's medical history blocks.

