"""
Automated Patient Medication Reminders
Workflow 1: Checks patient medication schedules in the database and dispatches
automated WhatsApp reminders when doses are due, preventing duplicate alerts
and supporting background scheduled execution via APScheduler.
"""

import sys
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

# Ensure backend root is in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from whatsapp_service import send_whatsapp, sanitize_phone_number
from sms_service import send_sms_msg91

# Configure logger
logger = logging.getLogger("MedicationReminders")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Global APScheduler instance
_SCHEDULER = None


def send_medication_reminder(
    patient_phone: str,
    medication_name: str,
    scheduled_time: str,
    dosage: str = "",
    patient_name: str = ""
) -> Dict[str, Any]:
    """
    Sends an automated WhatsApp medication reminder to the patient.
    
    Example Message:
    "Reminder: Your scheduled Metformin 500mg (1 tablet) dose is due at 8:00 PM.
     Please follow your prescribed medication plan."
    """
    clean_phone = sanitize_phone_number(patient_phone)
    if not clean_phone:
        logger.error(f"Cannot send medication reminder: invalid phone '{patient_phone}'")
        return {
            "success": False,
            "error": f"Invalid phone number: '{patient_phone}'",
            "medication": medication_name,
            "scheduled_time": scheduled_time
        }

    dosage_str = f" ({dosage.strip()})" if dosage and dosage.strip() else ""
    patient_greeting = f"Hello {patient_name.strip()},\n" if patient_name and patient_name.strip() else ""

    message = (
        f"{patient_greeting}"
        f"Reminder: Your scheduled {medication_name.strip()}{dosage_str} dose is due at {scheduled_time.strip()}. "
        f"Please follow your prescribed medication plan."
    )

    logger.info(f"Dispatching medication reminder for '{medication_name}' to {clean_phone}...")
    tmpl_name = os.getenv("WHATSAPP_TEMPLATE_MEDICATION_REMINDER")
    tmpl_params = [f"{medication_name.strip()}{dosage_str}", scheduled_time.strip()] if tmpl_name else None

    res = send_whatsapp(
        phone_number=clean_phone,
        message=message,
        template_name=tmpl_name,
        template_params=tmpl_params
    )

    # Automated MSG91 SMS Dispatch to patient
    sms_vars = {
        "patient_name": patient_name or "Patient",
        "medication_name": f"{medication_name.strip()}{dosage_str}",
        "time": scheduled_time.strip(),
        "message": message[:160]
    }
    sms_res = send_sms_msg91(
        recipient_phone=clean_phone,
        message=message,
        flow_id=os.getenv("MSG91_FLOW_ID_MEDICATION"),
        template_variables=sms_vars
    )
    res["sms_result"] = sms_res
    res["medication_name"] = medication_name
    res["scheduled_time"] = scheduled_time
    res["dosage"] = dosage
    return res


def get_database_session():
    """Retrieves a SQLAlchemy session from backend.app.database if available."""
    try:
        from app.database import SessionLocal, engine, Base
        import app.models  # ensure models are registered
        Base.metadata.create_all(bind=engine)
        return SessionLocal()
    except Exception as e:
        logger.warning(f"Could not initialize app database session: {e}")
        return None


def check_and_send_due_reminders(db=None, current_time_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Reads active medication schedules from the database, identifies doses due now,
    and dispatches one reminder per due dose while preventing duplicate alerts.
    
    Deduplication Rule:
    - Compares today's date (YYYY-MM-DD) against schedule.last_reminded_date.
    - If already sent today for this time window, skips duplicate sending.
    """
    close_db_on_exit = False
    if db is None:
        db = get_database_session()
        close_db_on_exit = True

    if db is None:
        logger.warning("No database session available to check medication schedules.")
        return []

    dispatched = []
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    current_hhmm = current_time_str or now.strftime("%H:%M")

    try:
        from app.models import MedicationSchedule, User

        # Query all active medication schedules
        schedules = db.query(MedicationSchedule).filter(MedicationSchedule.is_active == True).all()

        for sched in schedules:
            # Parse scheduled time
            sched_time = (sched.scheduled_time or "").strip()
            
            # Match current hour/minute window (or close within +/- 5 minutes)
            # Normalize e.g. "8:00" to "08:00"
            norm_sched = sched_time.zfill(5) if len(sched_time) == 4 and ":" in sched_time else sched_time
            norm_curr = current_hhmm.zfill(5) if len(current_hhmm) == 4 and ":" in current_hhmm else current_hhmm

            # Check if due now and not yet reminded today
            is_due = (norm_sched == norm_curr)
            already_reminded_today = (sched.last_reminded_date == today_str)

            if is_due and not already_reminded_today:
                # Find patient phone number
                phone = sched.patient_phone
                patient_name = "Patient"
                if not phone and sched.patient_id:
                    user = db.query(User).filter(User.id == sched.patient_id).first()
                    if user:
                        phone = user.phone
                        patient_name = user.full_name or "Patient"

                if not phone:
                    phone = os.getenv("DEFAULT_ALERT_RECIPIENT", "+919876543210")

                result = send_medication_reminder(
                    patient_phone=phone,
                    medication_name=sched.medication_name,
                    scheduled_time=sched.scheduled_time,
                    dosage=sched.dosage or "",
                    patient_name=patient_name
                )

                # Update schedule record to prevent duplicate reminders today
                sched.last_reminded_date = today_str
                sched.last_status = "SENT" if result.get("success") else "FAILED"
                db.commit()

                dispatched.append({
                    "schedule_id": sched.id,
                    "patient_id": sched.patient_id,
                    "medication": sched.medication_name,
                    "phone": phone,
                    "result": result
                })
                logger.info(f"Recorded reminder dispatch for schedule #{sched.id} ({sched.medication_name}).")

    except Exception as e:
        logger.error(f"Error checking due medication schedules: {e}")
    finally:
        if close_db_on_exit and db is not None:
            db.close()

    return dispatched


def start_medication_scheduler(interval_seconds: int = 60):
    """
    Initializes and starts background APScheduler worker to monitor medication schedules.
    Runs every interval_seconds (default: every 60 seconds).
    """
    global _SCHEDULER
    if _SCHEDULER is not None and _SCHEDULER.running:
        logger.info("Medication reminder scheduler is already running.")
        return _SCHEDULER

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        _SCHEDULER = BackgroundScheduler(daemon=True)
        _SCHEDULER.add_job(
            check_and_send_due_reminders,
            "interval",
            seconds=interval_seconds,
            id="check_due_medication_reminders",
            replace_existing=True
        )
        _SCHEDULER.start()
        logger.info(f"APScheduler background worker started (checking schedules every {interval_seconds}s).")
        return _SCHEDULER
    except Exception as e:
        logger.error(f"Failed to start APScheduler: {e}")
        return None


def stop_medication_scheduler():
    """Gracefully stops the background scheduler."""
    global _SCHEDULER
    if _SCHEDULER is not None and _SCHEDULER.running:
        _SCHEDULER.shutdown(wait=False)
        logger.info("Medication reminder scheduler stopped.")
        _SCHEDULER = None


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("   AUTOMATED PATIENT MEDICATION REMINDER - TEST RUN")
    print("=" * 70)

    test_phone = os.getenv("DEFAULT_ALERT_RECIPIENT", "+919876543210")
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        test_phone = sys.argv[1].strip()

    print(f"\n1. SENDING IMMEDIATE TEST REMINDER TO: {test_phone}")
    res = send_medication_reminder(
        patient_phone=test_phone,
        medication_name="Metformin 500mg",
        scheduled_time="08:00 AM",
        dosage="1 tablet with breakfast",
        patient_name="Yogesh"
    )

    print("\n2. DISPATCH RESULT:")
    print(f"   * Success : {res.get('success')}")
    print(f"   * Status  : {res.get('status')}")
    print(f"   * SID     : {res.get('sid')}")
    if res.get("error"):
        print(f"   * Error   : {res.get('error')}")

    print("\n3. CHECKING DATABASE SCHEDULES FOR DUE DOSES:")
    due = check_and_send_due_reminders()
    print(f"   * Due schedules processed: {len(due)}")

    print("\n" + "=" * 70)
    print("[COMPLETE] Medication reminder test execution finished.")
    print("=" * 70)
