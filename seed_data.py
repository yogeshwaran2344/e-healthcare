"""
Database Seeder for AI Personal Health Navigator.
Populates realistic demo accounts:
- Doctors with different specialties
- Demo Patient with pre-existing Diabetes, Hypertension, and Penicillin allergy
  (to showcase the Medication Safety Checker and Clinical Handover)
"""

import json
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import User, DoctorProfile, Consultation, Prescription
from backend.app.auth import hash_password
from backend.app.ml.handover_engine import generate_sbar_handover

def seed_patentable_addons(patient, doctor, db, consultation=None):
    from backend.app.models import (
        IoTDevice, IoTVitalReading, BlockchainBlock, ConsentRecord,
        QueueToken, EmergencyAlert, CommunityPost, PreventiveChallenge,
        PatientReward, PredictiveFollowUp, ChronicAlert
    )
    from backend.app.ml.blockchain_engine import create_block, generate_consent_token
    from backend.app.ml.iot_engine import IOT_DEVICE_CATALOG, generate_telemetry_reading
    from backend.app.ml.community_preventive_engine import DEFAULT_PREVENTIVE_CHALLENGES, SUPPORT_GROUPS_CATALOG
    from datetime import datetime, timedelta

    # A. IoT Devices & Readings
    for cat in IOT_DEVICE_CATALOG:
        d = IoTDevice(
            patient_id=patient.id,
            device_name=cat["device_name"],
            device_type=cat["device_type"],
            device_uid=f"{cat['device_uid']}-{patient.id}",
            firmware_version=cat["firmware"],
            battery_level=92,
            connection_status="connected",
            last_sync_at=datetime.utcnow()
        )
        db.add(d)
        db.flush()

        # Seed initial baseline reading
        synth = generate_telemetry_reading(d.device_type, simulate_anomaly=False)
        ecg_json = json.dumps(synth["ecg_waveform_points"]) if synth["ecg_waveform_points"] else None
        reading = IoTVitalReading(
            patient_id=patient.id,
            device_id=d.id,
            metric_type=synth["metric_type"],
            primary_value=synth["primary_value"],
            secondary_value=synth["secondary_value"],
            unit=synth["unit"],
            is_anomaly=synth["is_anomaly"],
            alert_severity=synth["alert_severity"],
            alert_message=synth["alert_message"],
            ecg_waveform_points=ecg_json,
            recorded_at=datetime.utcnow()
        )
        db.add(reading)

    # B. Blockchain Genesis & Consultation Blocks
    genesis_dict = create_block(
        block_index=0,
        patient_id=patient.id,
        record_type="GENESIS",
        record_id="GENESIS-ANCHOR",
        data_dict={"title": "Patient Health Ledger Genesis Anchor", "legal": "HIPAA/GDPR Sovereign Record"},
        previous_hash="0" * 64
    )
    genesis_b = BlockchainBlock(**genesis_dict)
    db.add(genesis_b)
    db.flush()

    c_id = consultation.id if consultation else 1
    c_block_dict = create_block(
        block_index=1,
        patient_id=patient.id,
        record_type="CONSULTATION",
        record_id=str(c_id),
        data_dict={"condition": "Pneumonia", "triage": "Doctor Consultation", "confidence": 96.5},
        previous_hash=genesis_b.block_hash
    )
    db.add(BlockchainBlock(**c_block_dict))

    # Consent Records
    token_doc, exp_doc = generate_consent_token("doc", 168)
    db.add(ConsentRecord(
        patient_id=patient.id,
        grantee_name="Dr. Sarah Sharma",
        grantee_type="doctor",
        grantee_organization="Apex Multi-Specialty Hospital",
        permissions=json.dumps(["diagnoses", "lab_reports", "prescriptions", "live_vitals"]),
        access_token=token_doc,
        status="active",
        expires_at=exp_doc
    ))

    # C. Smart Queue Token
    db.add(QueueToken(
        token_code="A-114",
        patient_id=patient.id,
        doctor_id=doctor.id,
        department="OPD Pulmonology & Critical Care",
        priority_level="NORMAL",
        status="waiting",
        queue_number=14,
        estimated_wait_minutes=12
    ))

    # D. Predictive Care & Chronic Alerts
    db.add(PredictiveFollowUp(
        patient_id=patient.id,
        consultation_id=c_id,
        risk_score=58.5,
        urgency_level="Moderate",
        suggested_timeline="Within 3 to 5 days",
        urgency_rationale="Active Type 2 Diabetes compounds infection vulnerability | Pre-existing Hypertension | Stage 1 Pneumonia Handover",
        recommended_specialist="Attending Pulmonologist / Critical Care",
        suggested_date=(datetime.now() + timedelta(days=3)).strftime("%A, %b %d, %Y"),
        status="suggested"
    ))
    db.add(ChronicAlert(
        patient_id=patient.id,
        condition_name="Type 2 Diabetes",
        trigger_source="AI Multi-Factor Analysis",
        alert_title="Hyperglycemia Vigilance Alert",
        clinical_implication="Infection stress may elevate fasting blood glucose above 180 mg/dL.",
        recommended_action="Maintain 3x daily glucose logs using connected CGM and hydrate adequately.",
        severity="WARNING",
        is_active=True
    ))
    db.add(ChronicAlert(
        patient_id=patient.id,
        condition_name="Drug Allergy Barrier",
        trigger_source="Patient Profile Safety Cross-Match",
        alert_title="Active Allergy Shield: Penicillin / Amoxicillin",
        clinical_implication="Severe IgE allergy to Penicillins. Antibiotic crossover prohibited.",
        recommended_action="Safety filter will automatically mandate Macrolide or Fluoroquinolone alternatives.",
        severity="INFO",
        is_active=True
    ))

    # E. Preventive Challenges & Rewards
    for c in DEFAULT_PREVENTIVE_CHALLENGES:
        db.add(PreventiveChallenge(
            patient_id=patient.id,
            challenge_key=c["challenge_key"],
            title=c["title"],
            description=c["description"],
            target_value=c["target_value"],
            current_value=c["current_value"],
            unit=c["unit"],
            streak_days=4,
            points_reward=c["points_reward"],
            is_completed=c["current_value"] >= c["target_value"]
        ))

    db.add(PatientReward(
        patient_id=patient.id,
        total_points=480,
        tier_level="Gold Vitality Member",
        badges_json=json.dumps([
            {"name": "Hydration Hero", "desc": "Reached 2.5L daily target 7 days consecutively", "icon": "bi-droplet-fill", "color": "info"},
            {"name": "Glucose Guardian", "desc": "100% adherence to glycemic self-monitoring", "icon": "bi-heart-pulse-fill", "color": "danger"},
            {"name": "10k Stepper", "desc": "Completed 50,000 steps across 5 days", "icon": "bi-lightning-charge-fill", "color": "warning"},
            {"name": "Blockchain Sovereign", "desc": "Verified ownership of encrypted health records", "icon": "bi-shield-lock-fill", "color": "primary"}
        ])
    ))

    # F. Community Posts
    db.add(CommunityPost(
        author_id=patient.id,
        group_slug="diabetes_warriors",
        group_name="Type 2 Diabetes Warriors & CGM Circle",
        title="Continuous glucose monitoring tip for breakfast spikes",
        content="I started eating boiled eggs and avocado before having my oatmeal, and my postprandial glucose spike decreased from 195 to 132 mg/dL. Huge improvement!",
        ai_safety_score=98.5,
        ai_moderation_status="approved",
        ai_moderation_notes="AI Verified Safe: Context aligns with supportive peer sharing. No contraindications detected.",
        is_ai_verified=True,
        likes_count=19
    ))
    db.commit()

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:

        # Check if already seeded
        existing_doc = db.query(User).filter(User.email == "doctor@example.com").first()
        if existing_doc:
            p = db.query(User).filter(User.email == "patient@example.com").first()
            if p:
                if not p.drug_allergies:
                    p.age = 48
                    p.gender = "Male"
                    p.blood_group = "B+"
                    p.pre_existing_conditions = "Diabetes Type 2, Mild Hypertension"
                    p.current_medications = "Metformin 500mg (OD), Telmisartan 40mg"
                    p.drug_allergies = "Penicillin, Amoxicillin"
                    db.commit()

                # Check if patentable add-ons exist
                from backend.app.models import IoTDevice
                dev = db.query(IoTDevice).filter(IoTDevice.patient_id == p.id).first()
                if not dev:
                    print("Seeding patentable add-ons for existing patient profile...")
                    seed_patentable_addons(p, existing_doc, db)
                    print("Patentable add-ons seeded successfully.")
                else:
                    print("Database already contains seed data and patentable add-ons.")
            return


        print("Seeding medical specialists and patient profile...")

        # 1. Doctors
        doctors_info = [
            {
                "name": "Dr. Sarah Sharma",
                "email": "doctor@example.com",
                "password": "doctor123",
                "phone": "+91 98765 43210",
                "specialization": "Pulmonologist & Critical Care",
                "qualification": "MBBS, MD (Pulmonary Medicine)",
                "license": "MCI-48921",
                "experience": 11,
                "hospital": "Apex Multi-Specialty Hospital",
                "bio": "Specialist in respiratory illnesses, pneumonia, asthma, and infectious pulmonary conditions."
            },
            {
                "name": "Dr. Rajesh Mehta",
                "email": "rajesh.cardio@example.com",
                "password": "doctor123",
                "phone": "+91 98765 43211",
                "specialization": "Cardiologist",
                "qualification": "MBBS, MD, DM (Cardiology)",
                "license": "MCI-31245",
                "experience": 14,
                "hospital": "Metro Heart & Vascular Institute",
                "bio": "Expert in cardiovascular health, hypertension, angina, and preventive cardiology."
            },
            {
                "name": "Dr. Ananya Iyer",
                "email": "ananya.gp@example.com",
                "password": "doctor123",
                "phone": "+91 98765 43212",
                "specialization": "General Physician",
                "qualification": "MBBS, DNB (Family Medicine)",
                "license": "MCI-65239",
                "experience": 8,
                "hospital": "City Care Clinic",
                "bio": "Primary care physician managing fevers, viral infections, metabolic disorders, and health screenings."
            }
        ]

        created_doctors = []
        for d in doctors_info:
            user = User(
                full_name=d["name"],
                email=d["email"],
                password_hash=hash_password(d["password"]),
                role="doctor",
                phone=d["phone"]
            )
            db.add(user)
            db.flush()

            profile = DoctorProfile(
                user_id=user.id,
                specialization=d["specialization"],
                qualification=d["qualification"],
                license_number=d["license"],
                experience_years=d["experience"],
                hospital_affiliation=d["hospital"],
                bio=d["bio"]
            )
            db.add(profile)
            created_doctors.append(user)

        # 2. Demo Patient with Chronic Profile
        patient = User(
            full_name="Rahul Verma",
            email="patient@example.com",
            password_hash=hash_password("patient123"),
            role="patient",
            phone="+91 91234 56789",
            age=48,
            gender="Male",
            blood_group="B+",
            pre_existing_conditions="Diabetes Type 2, Mild Hypertension",
            current_medications="Metformin 500mg, Telmisartan 40mg",
            drug_allergies="Penicillin, Amoxicillin"
        )
        db.add(patient)
        db.flush()

        # 3. Demo Consultation with Handover
        sample_symptoms = ["high_fever", "productive_cough_phlegm", "breathlessness_shortness_of_breath", "chest_tightness"]
        qa_data = {
            "duration_days": "3-5 days (persistent)",
            "severity_scale": "7 - 8 (Severe, causing significant distress)",
            "specific_fever": "Moderate (101-102°F) with shivering",
            "specific_cough": "Deep chest cough with yellow or green phlegm",
            "prior_meds_taken": "Paracetamol / Acetaminophen (fever/pain)"
        }
        bio_data = {
            "extracted_parameters": {"WBC Count": "13,800 /µL", "CRP": "12.4 mg/L", "Platelet Count": "195,000 /µL"},
            "abnormal_flags": ["High WBC (13,800 /µL - Leukocytosis / Active Infection)"],
            "radiology_findings": ["Dense patchy infiltration / consolidation observed in lung fields (Consistent with Pneumonia)"]
        }
        xai_factors = [
            "Matched 4 core symptoms: high fever, productive cough phlegm, breathlessness, chest tightness.",
            "Elevated white blood cell count (leukocytosis) in uploaded report indicates active bacterial infection.",
            "Radiology/Chest scan findings show lung opacity consistent with pneumonia consolidation.",
            "Pre-existing Diabetes increases vulnerability to lower respiratory tract infections."
        ]

        handover = generate_sbar_handover(
            patient_info={
                "full_name": patient.full_name,
                "age": patient.age,
                "gender": patient.gender,
                "pre_existing_conditions": patient.pre_existing_conditions,
                "current_medications": patient.current_medications,
                "drug_allergies": patient.drug_allergies
            },
            symptoms=sample_symptoms,
            qa_answers=qa_data,
            predicted_disease="Pneumonia",
            confidence=96.5,
            triage_data={"triage_level": "Doctor Consultation"},
            biomarkers=bio_data,
            patient_notes="Experiencing heavy coughing with yellow phlegm and fever for 3 days. Shortness of breath when climbing stairs."
        )

        consultation = Consultation(
            patient_id=patient.id,
            doctor_id=created_doctors[0].id,
            symptoms_list=json.dumps(sample_symptoms),
            predicted_disease="Pneumonia",
            confidence_score=96.5,
            recommended_tests="Chest X-Ray, Complete Blood Count (CBC)",
            severity="Moderate to High",
            triage_level="Doctor Consultation",
            adaptive_qa=json.dumps(qa_data),
            extracted_biomarkers=json.dumps(bio_data),
            xai_reasoning=json.dumps(xai_factors),
            clinical_handover_summary=json.dumps(handover),
            patient_notes="Experiencing heavy coughing with yellow phlegm and fever for 3 days. Shortness of breath when climbing stairs.",
            status="pending"
        )
        db.add(consultation)
        db.flush()

        # 4. Seed Patentable Add-Ons
        seed_patentable_addons(patient, created_doctors[0], db, consultation)
        db.commit()
        print("Database successfully seeded with AI Personal Health Navigator + 6 Patentable Add-Ons!")

        print("Database successfully seeded with AI Personal Health Navigator + 6 Patentable Add-Ons!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
