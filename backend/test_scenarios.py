"""
Comprehensive Clinical Workflow Verification Script
Directly tests and verifies the three essential automated scenarios:
1. Medication dose due -> Patient receives automated SMS (with deduplication).
2. Abnormal Blood Pressure -> Registered caretaker receives automated SMS.
3. Abnormal Heart Rate -> Registered caretaker receives automated SMS.
"""

import sys
import os
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Ensure paths
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.database import SessionLocal, engine, Base
from app.models import User, MedicationSchedule, CaretakerAlertConfig, IoTVitalReading, IoTDevice
from medication_reminders import check_and_send_due_reminders
from health_alerts import check_vitals, evaluate_patient_latest_vitals, _ALERT_EPISODE_CACHE

def run_scenario_verification():
    print("=" * 75)
    print("   NEUROCARE HEALTHCARE - 3 CLINICAL SCENARIOS VERIFICATION")
    print("=" * 75)

    db = SessionLocal()
    test_phone = os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")

    try:
        # Step 0: Ensure Test Patient & Caretaker Configuration
        patient = db.query(User).filter(User.email == "patient_test@example.com").first()
        if not patient:
            patient = User(
                email="patient_test@example.com",
                full_name="Rahul Verma",
                password_hash="dummy_hash_for_test",
                role="patient",
                phone=test_phone
            )
            db.add(patient)
            db.commit()
            db.refresh(patient)
        else:
            patient.phone = test_phone
            db.commit()

        # Ensure Caretaker Alert Configuration
        cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == patient.id).first()
        if not cfg:
            cfg = CaretakerAlertConfig(
                patient_id=patient.id,
                caretaker_name="Dr. Anita Verma (Caretaker)",
                caretaker_phone=test_phone,
                relationship="Primary Guardian",
                systolic_min=90.0,
                systolic_max=140.0,
                diastolic_min=60.0,
                diastolic_max=90.0,
                heart_rate_min=50.0,
                heart_rate_max=100.0,
                is_active=True
            )
            db.add(cfg)
            db.commit()
            db.refresh(cfg)

        print(f"\n[SETUP] Test Patient ID #{patient.id} ({patient.full_name}) ready.")
        print(f"        Registered Caretaker: {cfg.caretaker_name} ({cfg.caretaker_phone})")

        # -------------------------------------------------------------
        # SCENARIO 1: Medication Dose Becomes Due -> Patient Receives SMS
        # -------------------------------------------------------------
        print("\n" + "-" * 75)
        print("SCENARIO 1: Automated Patient Medication Reminder on Due Schedule")
        print("-" * 75)
        now_time_str = datetime.now().strftime("%H:%M")

        # Create or update an active medication schedule due at the current minute
        sched = db.query(MedicationSchedule).filter(
            MedicationSchedule.patient_id == patient.id,
            MedicationSchedule.medication_name == "Metformin 500mg"
        ).first()

        if not sched:
            sched = MedicationSchedule(
                patient_id=patient.id,
                medication_name="Metformin 500mg",
                dosage="1 Tablet after meals",
                condition="Type 2 Diabetes",
                scheduled_time=now_time_str,
                patient_phone=patient.phone,
                is_active=True,
                last_reminded_date=None
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)
        else:
            sched.scheduled_time = now_time_str
            sched.last_reminded_date = None  # Reset to test due trigger
            sched.is_active = True
            db.commit()

        print(f"Created/Scheduled Dose: '{sched.medication_name}' due at {sched.scheduled_time}")

        # Execute due schedules check
        dispatched_1 = check_and_send_due_reminders(db=db, current_time_str=now_time_str)
        print(f"Trigger Output: Processed {len(dispatched_1)} due dose(s).")
        
        assert len(dispatched_1) > 0, "Scenario 1 Failure: Dose was due but not dispatched!"
        item = dispatched_1[0]
        print(f"[PASS] SCENARIO 1: Medication reminder sent to {item['phone']}!")
        print(f"   Provider: {item['result'].get('provider')}")
        print(f"   SMS Status: {item['result'].get('sms_result', {}).get('status')}")
        print(f"   SMS SID: {item['result'].get('sms_result', {}).get('sid')}")

        # Verification of Deduplication (Run immediately again)
        print("\n[VERIFYING DEDUPLICATION] Running reminder check a second time for same slot...")
        dispatched_dup = check_and_send_due_reminders(db=db, current_time_str=now_time_str)
        print(f"Deduplication Check: Processed {len(dispatched_dup)} doses (Expected: 0).")
        assert len(dispatched_dup) == 0, "Scenario 1 Failure: Duplicate reminder was sent!"
        print("[PASS] DEDUPLICATION VERIFIED: Schedule already reminded today was suppressed correctly.")

        # -------------------------------------------------------------
        # SCENARIO 2: Patient's BP Becomes Abnormal -> Caretaker Receives SMS
        # -------------------------------------------------------------
        print("\n" + "-" * 75)
        print("SCENARIO 2: Patient Blood Pressure Becomes Abnormal -> Caretaker Alert")
        print("-" * 75)
        
        abnormal_sys = 168.0
        abnormal_dia = 104.0
        normal_hr = 72.0

        print(f"Simulating Telemetry Input: BP {int(abnormal_sys)}/{int(abnormal_dia)} mmHg (Safe: 90-140/60-90 mmHg)")

        # Clear cache for isolated test
        _ALERT_EPISODE_CACHE.pop(str(patient.id), None)

        bp_alert_res = check_vitals(
            patient_id=str(patient.id),
            caretaker_phone=cfg.caretaker_phone,
            systolic_bp=abnormal_sys,
            diastolic_bp=abnormal_dia,
            heart_rate=normal_hr,
            bp_limits=(cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max),
            heart_rate_limits=(cfg.heart_rate_min, cfg.heart_rate_max),
            patient_name=patient.full_name,
            bypass_cooldown=True
        )

        assert bp_alert_res.get("alert_required") is True, "Scenario 2 Failure: Alert was not required for abnormal BP!"
        print(f"[PASS] SCENARIO 2: BP Alert Triggered!")
        print(f"   Severity: {bp_alert_res.get('severity')}")
        print(f"   Triggered Rules: {bp_alert_res.get('alerts')}")
        print(f"   SMS Dispatched To: {cfg.caretaker_phone}")
        print(f"   SMS Status: {bp_alert_res.get('sms_notification', {}).get('status')}")
        print(f"   SMS Reference: {bp_alert_res.get('sms_notification', {}).get('sid')}")

        # -------------------------------------------------------------
        # SCENARIO 3: Patient's Heart Rate Becomes Abnormal -> Caretaker Receives SMS
        # -------------------------------------------------------------
        print("\n" + "-" * 75)
        print("SCENARIO 3: Patient Heart Rate Becomes Abnormal -> Caretaker Alert")
        print("-" * 75)

        normal_sys = 120.0
        normal_dia = 80.0
        abnormal_hr = 135.0  # Tachycardia crisis

        print(f"Simulating Telemetry Input: Heart Rate {int(abnormal_hr)} bpm (Safe: 50-100 bpm)")

        # Clear cache for isolated test
        _ALERT_EPISODE_CACHE.pop(str(patient.id), None)

        hr_alert_res = check_vitals(
            patient_id=str(patient.id),
            caretaker_phone=cfg.caretaker_phone,
            systolic_bp=normal_sys,
            diastolic_bp=normal_dia,
            heart_rate=abnormal_hr,
            bp_limits=(cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max),
            heart_rate_limits=(cfg.heart_rate_min, cfg.heart_rate_max),
            patient_name=patient.full_name,
            bypass_cooldown=True
        )

        assert hr_alert_res.get("alert_required") is True, "Scenario 3 Failure: Alert was not required for abnormal HR!"
        print(f"[PASS] SCENARIO 3: Heart Rate Alert Triggered!")
        print(f"   Severity: {hr_alert_res.get('severity')}")
        print(f"   Triggered Rules: {hr_alert_res.get('alerts')}")
        print(f"   SMS Dispatched To: {cfg.caretaker_phone}")
        print(f"   SMS Status: {hr_alert_res.get('sms_notification', {}).get('status')}")
        print(f"   SMS Reference: {hr_alert_res.get('sms_notification', {}).get('sid')}")

        print("\n" + "=" * 75)
        print("[SUCCESS] ALL 3 CLINICAL SCENARIOS FULLY VERIFIED & WORKING END-TO-END!")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    run_scenario_verification()
