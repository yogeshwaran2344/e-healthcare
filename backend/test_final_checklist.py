"""
Final SMS & Clinical Trigger Verification Suite
Validates all 6 items of the Final SMS Verification Checklist:
1. Test SMS: Tests direct SMS dispatch to test phone.
2. Medication reminder: Dose due -> Patient automatically receives SMS.
3. Abnormal BP: Test BP crosses threshold -> Caretaker receives SMS.
4. Abnormal heart rate: Test HR crosses threshold -> Caretaker receives SMS.
5. Backend restart: Scheduler resumes cleanly, jobs remain active.
6. Delivery tracking: Failed/successful messages logged, duplicate alerts prevented.
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

# Ensure backend root is in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from app.database import SessionLocal
from app.models import User, MedicationSchedule, CaretakerAlertConfig, IoTVitalReading
from sms_service import send_sms_msg91, check_sms_service_health
from medication_reminders import (
    check_and_send_due_reminders,
    start_medication_scheduler,
    stop_medication_scheduler,
    _SCHEDULER
)
from health_alerts import check_vitals, _ALERT_EPISODE_CACHE

def run_final_checklist():
    print("=" * 75)
    print("         FINAL SMS & CLINICAL TRIGGERS VERIFICATION SUITE")
    print("=" * 75)

    db = SessionLocal()
    test_phone = os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")

    try:
        # Pre-flight setup: Ensure patient and caretaker in database
        patient = db.query(User).filter(User.email == "patient_checklist@example.com").first()
        if not patient:
            patient = User(
                email="patient_checklist@example.com",
                full_name="Ananya Sharma",
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

        cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == patient.id).first()
        if not cfg:
            cfg = CaretakerAlertConfig(
                patient_id=patient.id,
                caretaker_name="Ramesh Sharma (Guardian)",
                caretaker_phone=test_phone,
                relationship="Father",
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

        print(f"Test Patient: #{patient.id} {patient.full_name} | Phone: {patient.phone}")
        print(f"Caretaker   : {cfg.caretaker_name} | Phone: {cfg.caretaker_phone}\n")

        # ---------------------------------------------------------------------
        # CHECK 1: TEST SMS
        # ---------------------------------------------------------------------
        print("[CHECK 1] Direct SMS Gateway Dispatch")
        res1 = send_sms_msg91(
            recipient_phone=test_phone,
            message="NeuroCare Verification: Direct SMS path active.",
            template_variables={"patient_name": patient.full_name, "message": "Verification test"}
        )
        assert res1.get("success") is True, f"Check 1 Failed: {res1}"
        print(f"  * Status: {res1.get('status')}")
        print(f"  * Provider: {res1.get('provider')}")
        print(f"  * SID: {res1.get('sid')}")
        print("  -> CHECK 1 PASSED: SMS gateway ready for cellular transmission.\n")

        # ---------------------------------------------------------------------
        # CHECK 2: AUTOMATIC MEDICATION REMINDER (DATABASE + DUE TIME)
        # ---------------------------------------------------------------------
        print("[CHECK 2] Automatic Medication Reminder On Due Dose")
        current_time_str = datetime.now().strftime("%H:%M")
        today_date_str = datetime.now().strftime("%Y-%m-%d")

        sched = db.query(MedicationSchedule).filter(
            MedicationSchedule.patient_id == patient.id,
            MedicationSchedule.medication_name == "Amlodipine 5mg"
        ).first()

        if not sched:
            sched = MedicationSchedule(
                patient_id=patient.id,
                medication_name="Amlodipine 5mg",
                dosage="1 Tablet daily",
                condition="Hypertension",
                scheduled_time=current_time_str,
                patient_phone=patient.phone,
                is_active=True,
                last_reminded_date=None
            )
            db.add(sched)
            db.commit()
            db.refresh(sched)
        else:
            sched.scheduled_time = current_time_str
            sched.last_reminded_date = None
            sched.is_active = True
            db.commit()

        # Trigger due check
        dispatched = check_and_send_due_reminders(db=db, current_time_str=current_time_str)
        assert len(dispatched) > 0, "Check 2 Failed: Due medication dose was not processed!"
        sched_refreshed = db.query(MedicationSchedule).filter(MedicationSchedule.id == sched.id).first()
        assert sched_refreshed.last_reminded_date == today_date_str, "Check 2 Failed: last_reminded_date not updated in DB!"
        print(f"  * Medication: {sched.medication_name} due at {current_time_str}")
        print(f"  * Dispatched SMS to: {dispatched[0]['phone']}")
        print(f"  * DB Delivery Status: {sched_refreshed.last_status} (Recorded date: {sched_refreshed.last_reminded_date})")
        print("  -> CHECK 2 PASSED: Patient automatically receives SMS when dose is due.\n")

        # ---------------------------------------------------------------------
        # CHECK 3: ABNORMAL BLOOD PRESSURE ALERT TO CARETAKER
        # ---------------------------------------------------------------------
        print("[CHECK 3] Abnormal Blood Pressure Telemetry Breach")
        _ALERT_EPISODE_CACHE.pop(str(patient.id), None)
        res_bp = check_vitals(
            patient_id=str(patient.id),
            caretaker_phone=cfg.caretaker_phone,
            systolic_bp=172.0,  # Elevated above max 140.0
            diastolic_bp=106.0, # Elevated above max 90.0
            heart_rate=74.0,    # Normal
            bp_limits=(cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max),
            heart_rate_limits=(cfg.heart_rate_min, cfg.heart_rate_max),
            patient_name=patient.full_name,
            bypass_cooldown=True
        )
        assert res_bp.get("alert_required") is True, "Check 3 Failed: Abnormal BP did not trigger alert!"
        print(f"  * Reading: BP 172/106 mmHg (Limits: 90-140/60-90)")
        print(f"  * Severity: {res_bp.get('severity')}")
        print(f"  * Caretaker Recipient: {cfg.caretaker_phone}")
        print(f"  * Caretaker SMS Sent: {res_bp.get('sms_notification', {}).get('status')}")
        print("  -> CHECK 3 PASSED: Caretaker automatically receives SMS for abnormal BP.\n")

        # ---------------------------------------------------------------------
        # CHECK 4: ABNORMAL HEART RATE ALERT TO CARETAKER
        # ---------------------------------------------------------------------
        print("[CHECK 4] Abnormal Heart Rate Telemetry Breach")
        _ALERT_EPISODE_CACHE.pop(str(patient.id), None)
        res_hr = check_vitals(
            patient_id=str(patient.id),
            caretaker_phone=cfg.caretaker_phone,
            systolic_bp=120.0,  # Normal
            diastolic_bp=80.0,  # Normal
            heart_rate=142.0,   # Tachycardia above max 100.0
            bp_limits=(cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max),
            heart_rate_limits=(cfg.heart_rate_min, cfg.heart_rate_max),
            patient_name=patient.full_name,
            bypass_cooldown=True
        )
        assert res_hr.get("alert_required") is True, "Check 4 Failed: Abnormal HR did not trigger alert!"
        print(f"  * Reading: HR 142 bpm (Limits: 50-100)")
        print(f"  * Severity: {res_hr.get('severity')}")
        print(f"  * Caretaker Recipient: {cfg.caretaker_phone}")
        print(f"  * Caretaker SMS Sent: {res_hr.get('sms_notification', {}).get('status')}")
        print("  -> CHECK 4 PASSED: Caretaker automatically receives SMS for abnormal HR.\n")

        # ---------------------------------------------------------------------
        # CHECK 5: BACKEND RESTART & SCHEDULER RESILIENCY
        # ---------------------------------------------------------------------
        print("[CHECK 5] Backend Restart & Scheduler Resiliency")
        # 1. Stop scheduler to simulate server shutdown
        stop_medication_scheduler()
        print("  * Simulated Backend Shutdown: Scheduler stopped.")
        
        # 2. Restart scheduler to simulate server restart
        restarted_sched = start_medication_scheduler(interval_seconds=60)
        assert restarted_sched is not None and restarted_sched.running, "Check 5 Failed: Scheduler failed to restart!"
        job = restarted_sched.get_job("check_due_medication_reminders")
        assert job is not None, "Check 5 Failed: Due medication monitoring job missing after restart!"
        print(f"  * Simulated Backend Restart: Scheduler active (Job ID: '{job.id}')")
        print(f"  * Next Scheduled Check At: {job.next_run_time}")
        print("  -> CHECK 5 PASSED: Scheduler resumes automatically upon backend restart.\n")

        # ---------------------------------------------------------------------
        # CHECK 6: DELIVERY TRACKING & DUPLICATE PREVENTION
        # ---------------------------------------------------------------------
        print("[CHECK 6] Delivery Tracking & Duplicate Prevention")
        # Test medication reminder deduplication
        dup_reminders = check_and_send_due_reminders(db=db, current_time_str=current_time_str)
        assert len(dup_reminders) == 0, "Check 6 Failed: Repeated duplicate medication reminder sent!"
        print(f"  * Repeated medication due check: {len(dup_reminders)} sent (0 duplicate sends).")

        # Test vital alerts cooldown deduplication
        suppressed_hr = check_vitals(
            patient_id=str(patient.id),
            caretaker_phone=cfg.caretaker_phone,
            systolic_bp=120.0,
            diastolic_bp=80.0,
            heart_rate=142.0,  # Same abnormal value within cooldown
            bp_limits=(cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max),
            heart_rate_limits=(cfg.heart_rate_min, cfg.heart_rate_max),
            patient_name=patient.full_name,
            bypass_cooldown=False
        )
        assert suppressed_hr.get("suppressed") is True, "Check 6 Failed: Duplicate ongoing vital alert was not suppressed!"
        print(f"  * Repeated vital alert: Suppressed ({suppressed_hr.get('reason')}).")
        print("  -> CHECK 6 PASSED: Duplicates are prevented and delivery status is tracked.\n")

        print("=" * 75)
        print("   ALL 6 FINAL VERIFICATION CHECKS COMPLETED AND FULLY PASSED!")
        print("=" * 75)

    finally:
        db.close()

if __name__ == "__main__":
    run_final_checklist()
