"""
Seed Script for Adaptive Closed-Loop Clinical Decision & Verification System.
Populates realistic sample data for:
- Clinical Disagreement Records (with standard taxonomy)
- Verified Ground-Truth Clinical Outcomes (3-way reconciliation cases)
- Continuous Longitudinal Patient Health Timeline entries
- Contextual Emergency QR Tokens
"""

import os
import json
import datetime
from sqlalchemy.orm import Session
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    User, Consultation, ClinicalTimelineEntry,
    ClinicalDisagreementRecord, ClinicalOutcomeRecord, ContextualQRToken
)

def seed_closed_loop():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Fetch or verify patient and doctor exist
        patient = db.query(User).filter(User.role == "patient").first()
        doctor = db.query(User).filter(User.role == "doctor").first()

        if not patient or not doctor:
            print("Please ensure default users exist (run existing seed first if needed).")
            return

        print(f"Seeding closed-loop records for Patient: {patient.full_name} (ID: {patient.id}), Doctor: {doctor.full_name} (ID: {doctor.id})")

        # 1. Seed Longitudinal Digital Health Timeline
        existing_timeline = db.query(ClinicalTimelineEntry).filter(ClinicalTimelineEntry.patient_id == patient.id).count()
        if existing_timeline == 0:
            timeline_milestones = [
                {
                    "event_type": "symptom_report",
                    "title": "Initial Acute Onset: High Fever & Shivering Chills",
                    "description": "Patient reported acute high-grade fever (102.8°F) with headache and rigors. Emergency red-flags evaluated.",
                    "metrics": {"temp": "102.8°F", "heart_rate": "98 bpm", "pain_score": "6/10"},
                    "severity": "Moderate",
                    "days_ago": 60
                },
                {
                    "event_type": "lab_test",
                    "title": "Diagnostic Blood Panel: Platelet & Antigen Screening",
                    "description": "Lab report uploaded: Thrombocytopenia detected (platelets 88,000 /uL). Dengue NS1 Antigen tested positive.",
                    "metrics": {"platelets": "88,000 /uL", "wbc": "4,100 /uL", "ns1": "Positive"},
                    "severity": "Moderate",
                    "days_ago": 57
                },
                {
                    "event_type": "doctor_visit",
                    "title": "Teleconsultation & SBAR Handover Review",
                    "description": "Attending physician reviewed SBAR handover. Strict fluid therapy protocol initiated. NSAIDs contraindicated.",
                    "metrics": {"fluid_target": "3000 ml/day", "hematocrit": "42%"},
                    "severity": "Normal",
                    "days_ago": 56
                },
                {
                    "event_type": "prescription_issued",
                    "title": "Digital Prescription Signed: Hydration & Antipyretic Protocol",
                    "description": "Paracetamol 650mg TDS prescribed. Platelet surveillance scheduled at 12-hour intervals.",
                    "metrics": {"follow_up_days": 3},
                    "severity": "Normal",
                    "days_ago": 56
                },
                {
                    "event_type": "outcome_verified",
                    "title": "Clinical Outcome Verified: Full Recovery from Dengue",
                    "description": "Platelets rebounded to 210,000 /uL. Fever completely subsided. Closed-loop triangulation verified as Concordant Success.",
                    "metrics": {"final_platelets": "210,000 /uL", "status": "Resolved"},
                    "severity": "Normal",
                    "days_ago": 48
                },
                {
                    "event_type": "symptom_report",
                    "title": "Follow-Up Surveillance: Retrosternal Chest Heaviness",
                    "description": "Patient noted exertion-induced chest heaviness radiating to left shoulder after brisk walking.",
                    "metrics": {"bp": "142/92 mmHg", "pulse": "84 bpm"},
                    "severity": "Moderate",
                    "days_ago": 14
                }
            ]

            now = datetime.datetime.utcnow()
            for m in timeline_milestones:
                entry = ClinicalTimelineEntry(
                    patient_id=patient.id,
                    event_type=m["event_type"],
                    title=m["title"],
                    description=m["description"],
                    metrics_json=json.dumps(m["metrics"]),
                    severity_level=m["severity"],
                    recorded_at=now - datetime.timedelta(days=m["days_ago"])
                )
                db.add(entry)
            print(f"Added {len(timeline_milestones)} longitudinal health timeline entries.")

        # 2. Seed Clinical Disagreement Records
        existing_disag = db.query(ClinicalDisagreementRecord).count()
        if existing_disag == 0:
            disagreements = [
                {
                    "ai_pred": "Gastroesophageal Reflux (GERD) & Peptic Ulcer",
                    "ai_conf": 76.5,
                    "doc_diag": "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
                    "category": "ATYPICAL_PRESENTATION",
                    "grade": "CRITICAL_SAFETY_DIVERGENCE",
                    "rationale": "Patient reported burning epigastric discomfort mimicking acid reflux, but physical examination revealed diaphoresis, dyspnea on exertion, and ECG showed ST depression in inferior leads.",
                    "status": "reconciled"
                },
                {
                    "ai_pred": "Acute Viral Upper Respiratory Infection (Common Cold)",
                    "ai_conf": 81.0,
                    "doc_diag": "Bacterial Pneumonia / Lower Respiratory Infection",
                    "category": "PHYSICAL_EXAM_OVERRIDE",
                    "grade": "HIGH_CLINICAL_DIVERGENCE",
                    "rationale": "Chest auscultation detected localized unilateral crepitations and bronchial breathing at right lower base, not captured by digital symptom chips alone.",
                    "status": "reconciled"
                },
                {
                    "ai_pred": "Migraine with Aura / Cluster Headache",
                    "ai_conf": 68.0,
                    "doc_diag": "Acute Dengue Infection with Warning Signs",
                    "category": "EPIDEMIOLOGICAL_CONTEXT",
                    "grade": "MODERATE_DIAGNOSTIC_DIVERGENCE",
                    "rationale": "Local urban ward currently experiencing widespread Dengue cluster. Retro-orbital headache and thrombocytopenia prompt high suspicion despite absence of classic rash.",
                    "status": "pending_outcome"
                }
            ]

            for d in disagreements:
                rec = ClinicalDisagreementRecord(
                    consultation_id=1,
                    patient_id=patient.id,
                    doctor_id=doctor.id,
                    ai_predicted_disease=d["ai_pred"],
                    ai_confidence=d["ai_conf"],
                    ai_triage_level="Doctor Consultation",
                    doctor_diagnosed_disease=d["doc_diag"],
                    doctor_triage_level="Emergency Care" if "Emergency" in d["doc_diag"] else "Doctor Consultation",
                    discrepancy_category=d["category"],
                    severity_grade=d["grade"],
                    doctor_rationale=d["rationale"],
                    tests_considered_json=json.dumps(["12-Lead Electrocardiogram (ECG)", "High-Sensitivity Cardiac Troponin-I"]),
                    reconciliation_status=d["status"]
                )
                db.add(rec)
            print(f"Added {len(disagreements)} clinical disagreement audit records.")

        # 3. Seed Verified Clinical Outcomes (Closed Loop)
        existing_outcomes = db.query(ClinicalOutcomeRecord).count()
        if existing_outcomes == 0:
            outcomes = [
                {
                    "ai_pred": "Acute Dengue Infection with Warning Signs",
                    "doc_diag": "Acute Dengue Infection with Warning Signs",
                    "true_cond": "Acute Dengue Infection with Warning Signs",
                    "method": "Dengue NS1 Antigen & Platelet Count Blood Test",
                    "ai_correct": True,
                    "doc_correct": True,
                    "error_cat": "NO_ERROR",
                    "recon_type": "FULL_CONCORDANT_SUCCESS"
                },
                {
                    "ai_pred": "Gastroesophageal Reflux (GERD) & Peptic Ulcer",
                    "doc_diag": "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
                    "true_cond": "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
                    "method": "Coronary Angiography (85% LAD Stenosis)",
                    "ai_correct": False,
                    "doc_correct": True,
                    "error_cat": "ATYPICAL_PRESENTATION",
                    "recon_type": "PHYSICIAN_OVERRIDE_SAVED_ACCURACY"
                },
                {
                    "ai_pred": "Bacterial Pneumonia / Lower Respiratory Infection",
                    "doc_diag": "Acute Viral Upper Respiratory Infection (Common Cold)",
                    "true_cond": "Bacterial Pneumonia / Lower Respiratory Infection",
                    "method": "Chest X-Ray Consolidation & Sputum Culture",
                    "ai_correct": True,
                    "doc_correct": False,
                    "error_cat": "NO_ERROR",
                    "recon_type": "AI_PREDICTION_VINDICATED"
                },
                {
                    "ai_pred": "Acute Gastroenteritis & Dehydration",
                    "doc_diag": "Acute Gastroenteritis & Dehydration",
                    "true_cond": "Acute Cholecystitis / Gallstone Pathology",
                    "method": "Abdominal Ultrasound (USG) Gallstones with Wall Thickening",
                    "ai_correct": False,
                    "doc_correct": False,
                    "error_cat": "INSUFFICIENT_LAB_DATA",
                    "recon_type": "DUAL_DIAGNOSTIC_BLINDSPOT"
                }
            ]

            for o in outcomes:
                out_rec = ClinicalOutcomeRecord(
                    consultation_id=1,
                    patient_id=patient.id,
                    ai_predicted_disease=o["ai_pred"],
                    doctor_diagnosed_disease=o["doc_diag"],
                    confirmed_outcome_disease=o["true_cond"],
                    confirmation_method=o["method"],
                    days_to_resolution=5,
                    ai_was_correct=o["ai_correct"],
                    doctor_was_correct=o["doc_correct"],
                    error_category=o["error_cat"],
                    reconciliation_type=o["recon_type"],
                    calibration_feedback=f"Adjusted Bayesian prior weights for {o['true_cond']}."
                )
                db.add(out_rec)
            print(f"Added {len(outcomes)} verified clinical outcome records for closed loop.")

        # 4. Seed Dynamic Emergency QR Tokens
        existing_tokens = db.query(ContextualQRToken).filter(ContextualQRToken.patient_id == patient.id).count()
        if existing_tokens == 0:
            now = datetime.datetime.utcnow()
            scopes = [
                ("PUBLIC_BASIC", 1440, "public_token_demo_hash_98234"),
                ("AMBULANCE_PARAMEDIC", 60, "paramedic_token_demo_hash_44912"),
                ("HOSPITAL_ER_TRAUMA", 240, "er_trauma_token_demo_hash_11883")
            ]
            for scope, mins, t_hash in scopes:
                token = ContextualQRToken(
                    patient_id=patient.id,
                    token_hash=t_hash,
                    context_scope=scope,
                    expires_at=now + datetime.timedelta(minutes=mins),
                    access_count=1
                )
                db.add(token)
            print(f"Added {len(scopes)} contextual emergency tokens.")

        db.commit()
        print("Closed-loop seed completed successfully!")
    finally:
        db.close()

if __name__ == "__main__":
    seed_closed_loop()
