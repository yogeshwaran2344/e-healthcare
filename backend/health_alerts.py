"""
Caretaker Health Alerts Engine
Evaluates patient vital signs (Blood Pressure & Heart Rate) against
clinician-configured thresholds, validates sensor readings against artifacts,
and dispatches real-time cellular SMS alerts to registered caretakers with smart
deduplication and critical escalation support.
"""

import sys
import os
import math
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path

# Ensure backend root is in sys.path
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from sms_service import (
    send_sms,
    send_cellular_sms,
    sanitize_indian_mobile_number
)
from whatsapp_service import (
    send_whatsapp,
    format_whatsapp_recipient,
    format_whatsapp_url
)

# Configure logger
logger = logging.getLogger("HealthAlerts")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Default Clinical Reference Ranges (Configurable per patient)
# bp_limits: (systolic_min, systolic_max, diastolic_min, diastolic_max)
DEFAULT_BP_LIMITS: Tuple[float, float, float, float] = (90.0, 140.0, 60.0, 90.0)
# heart_rate_limits: (heart_rate_min, heart_rate_max)
DEFAULT_HR_LIMITS: Tuple[float, float] = (50.0, 100.0)

# Alert deduplication and escalation tracker
# Key: patient_id -> {"timestamp": datetime, "severity": str, "systolic": float, "hr": float}
_ALERT_EPISODE_CACHE: Dict[str, Dict[str, Any]] = {}
ALERT_COOLDOWN_MINUTES = 15


def validate_vital_reading(
    systolic_bp: float,
    diastolic_bp: float,
    heart_rate: float
) -> Tuple[bool, Optional[str]]:
    """
    Validates sensor telemetry for data integrity and physiological plausibility.
    Filters out disconnected sensor noise, NaN, or corrupted telemetry.
    """
    for name, val in [("systolic_bp", systolic_bp), ("diastolic_bp", diastolic_bp), ("heart_rate", heart_rate)]:
        if val is None or math.isnan(val) or math.isinf(val):
            return False, f"Sensor reading contains invalid or missing value for {name}."

    # Plausibility bounds
    if not (40.0 <= systolic_bp <= 300.0):
        return False, f"Systolic blood pressure ({systolic_bp} mmHg) is outside physiological bounds (40-300 mmHg)."
    if not (20.0 <= diastolic_bp <= 200.0):
        return False, f"Diastolic blood pressure ({diastolic_bp} mmHg) is outside physiological bounds (20-200 mmHg)."
    if diastolic_bp >= systolic_bp:
        return False, f"Diastolic pressure ({diastolic_bp}) cannot equal or exceed systolic pressure ({systolic_bp})."
    if not (25.0 <= heart_rate <= 260.0):
        return False, f"Heart rate ({heart_rate} bpm) is outside physiological bounds (25-260 bpm)."

    return True, None


def should_suppress_duplicate_alert(
    patient_id: str,
    severity: str,
    systolic_bp: float,
    heart_rate: float
) -> Tuple[bool, str]:
    """
    Deduplication logic:
    - Suppresses repeat alerts within the cooldown window (default 15 minutes) for the SAME severity tier.
    - Escalates immediately (bypasses cooldown) if:
        1. Severity escalates from WARNING to CRITICAL.
        2. Systolic BP spikes by >= 15 mmHg.
        3. Heart rate shifts by >= 20 bpm.
    """
    pid = str(patient_id)
    now = datetime.now(timezone.utc)
    cached = _ALERT_EPISODE_CACHE.get(pid)

    if not cached:
        return False, "Initial episode detected."

    elapsed_minutes = (now - cached["timestamp"]).total_seconds() / 60.0

    # If cooldown period has elapsed, allow new alert
    if elapsed_minutes >= ALERT_COOLDOWN_MINUTES:
        return False, f"Cooldown period ({ALERT_COOLDOWN_MINUTES}m) elapsed."

    # Escalation Rule 1: Severity escalated to CRITICAL
    if cached.get("severity") != "CRITICAL" and severity == "CRITICAL":
        return False, "Condition escalated to CRITICAL severity tier."

    # Escalation Rule 2: Significant clinical worsening
    old_sys = cached.get("systolic", 0.0)
    old_hr = cached.get("hr", 0.0)
    if (systolic_bp - old_sys) >= 15.0 or (old_sys - systolic_bp) >= 20.0:
        return False, f"Significant BP shift ({old_sys:.0f} -> {systolic_bp:.0f} mmHg)."
    if abs(heart_rate - old_hr) >= 20.0:
        return False, f"Significant Heart Rate shift ({old_hr:.0f} -> {heart_rate:.0f} bpm)."

    return True, f"Duplicate alert suppressed within {ALERT_COOLDOWN_MINUTES}m cooldown window."


def check_vitals(
    patient_id: str,
    caretaker_phone: str,
    systolic_bp: float,
    diastolic_bp: float,
    heart_rate: float,
    bp_limits: Tuple[float, float, float, float] = DEFAULT_BP_LIMITS,
    heart_rate_limits: Tuple[float, float] = DEFAULT_HR_LIMITS,
    patient_name: str = "",
    bypass_cooldown: bool = False
) -> Dict[str, Any]:
    """
    Evaluates patient vital signs against configured clinical thresholds.
    If thresholds are breached, dispatches a real-time cellular SMS alert to the registered caretaker.
    """
    # 1. Validate data integrity
    is_valid, validation_error = validate_vital_reading(systolic_bp, diastolic_bp, heart_rate)
    if not is_valid:
        logger.warning(f"Vital reading validation failed for patient {patient_id}: {validation_error}")
        return {
            "alert_required": False,
            "validation_passed": False,
            "error": validation_error
        }

    # 2. Check clinical thresholds
    alerts = []
    severity = "NORMAL"

    sys_min, sys_max, dia_min, dia_max = bp_limits
    hr_min, hr_max = heart_rate_limits

    # Blood Pressure Evaluation
    if systolic_bp > sys_max or diastolic_bp > dia_max:
        if systolic_bp >= 180.0 or diastolic_bp >= 120.0:
            alerts.append(f"Critical Hypertensive Crisis ({int(systolic_bp)}/{int(diastolic_bp)} mmHg, safe max: {int(sys_max)}/{int(dia_max)})")
            severity = "CRITICAL"
        else:
            alerts.append(f"Elevated Blood Pressure ({int(systolic_bp)}/{int(diastolic_bp)} mmHg, safe range: {int(sys_min)}-{int(sys_max)}/{int(dia_min)}-{int(dia_max)})")
            if severity != "CRITICAL":
                severity = "WARNING"
    elif systolic_bp < sys_min or diastolic_bp < dia_min:
        alerts.append(f"Hypotension Alert ({int(systolic_bp)}/{int(diastolic_bp)} mmHg, safe min: {int(sys_min)}/{int(dia_min)})")
        if severity != "CRITICAL":
            severity = "WARNING"

    # Heart Rate Evaluation
    if heart_rate > hr_max:
        if heart_rate >= 140.0:
            alerts.append(f"Critical Tachycardia ({int(heart_rate)} bpm, safe max: {int(hr_max)})")
            severity = "CRITICAL"
        else:
            alerts.append(f"Elevated Heart Rate ({int(heart_rate)} bpm, safe range: {int(hr_min)}-{int(hr_max)})")
            if severity != "CRITICAL":
                severity = "WARNING"
    elif heart_rate < hr_min:
        if heart_rate <= 45.0:
            alerts.append(f"Critical Bradycardia ({int(heart_rate)} bpm, safe min: {int(hr_min)})")
            severity = "CRITICAL"
        else:
            alerts.append(f"Low Heart Rate ({int(heart_rate)} bpm, safe range: {int(hr_min)}-{int(hr_max)})")
            if severity != "CRITICAL":
                severity = "WARNING"

    # If all vitals are within configured safe bounds, no alert required
    if not alerts:
        logger.info(f"Vitals within safe limits for patient {patient_id} (BP: {int(systolic_bp)}/{int(diastolic_bp)}, HR: {int(heart_rate)}).")
        return {
            "alert_required": False,
            "validation_passed": True,
            "severity": "NORMAL",
            "readings": {
                "systolic_bp": systolic_bp,
                "diastolic_bp": diastolic_bp,
                "heart_rate": heart_rate
            }
        }

    # 3. Deduplication and Cooldown Check
    pid_str = str(patient_id)
    if not bypass_cooldown:
        suppress, reason = should_suppress_duplicate_alert(pid_str, severity, systolic_bp, heart_rate)
        if suppress:
            logger.info(f"Caretaker SMS alert suppressed for patient {patient_id}: {reason}")
            return {
                "alert_required": True,
                "suppressed": True,
                "reason": reason,
                "severity": severity,
                "alerts": alerts
            }

    # 4. Construct SMS Message Body
    p_name = patient_name.strip() if patient_name else f"#{patient_id}"
    alerts_summary = "; ".join(alerts)
    message = (
        f"NeuroCare Health Alert [{severity}]: Patient {p_name} vitals out of range: "
        f"{alerts_summary}. Please check on the patient immediately."
    )

    clean_caretaker_phone = sanitize_indian_mobile_number(caretaker_phone)
    if not clean_caretaker_phone:
        clean_caretaker_phone = sanitize_indian_mobile_number(os.getenv("DEFAULT_ALERT_RECIPIENT", "8618912755"))

    # 5. Send Live Cellular SMS Alert to Caretaker
    logger.warning(f"Dispatching [{severity}] caretaker cellular SMS health alert for patient {patient_id} to +91{clean_caretaker_phone}...")

    dispatch_sms = send_cellular_sms(
        recipient_phone=clean_caretaker_phone,
        message=message
    )

    # 6. Update Episode Cache
    _ALERT_EPISODE_CACHE[pid_str] = {
        "timestamp": datetime.now(timezone.utc),
        "severity": severity,
        "systolic": systolic_bp,
        "hr": heart_rate,
        "last_status": dispatch_sms.get("status"),
        "sms_status": dispatch_sms.get("status")
    }

    return {
        "alert_required": True,
        "validation_passed": True,
        "severity": severity,
        "alerts": alerts,
        "message": message,
        "channel": "sms",
        "notification": dispatch_sms,
        "sms_notification": dispatch_sms,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


def evaluate_patient_latest_vitals(
    patient_id: int,
    db=None,
    systolic: Optional[float] = None,
    diastolic: Optional[float] = None,
    heart_rate: Optional[float] = None,
    bypass_cooldown: bool = False
) -> Dict[str, Any]:
    """
    Database bridge: looks up patient vitals and caretaker configuration from database,
    then executes check_vitals with patient-specific limits.
    Supports optional direct overrides for real-time sensor streams.
    """
    close_db = False
    if db is None:
        try:
            from app.database import SessionLocal
            db = SessionLocal()
            close_db = True
        except Exception as e:
            logger.warning(f"Database session unavailable: {e}")
            return {"error": "Database session unavailable"}

    try:
        from app.models import User, IoTVitalReading, CaretakerAlertConfig, FamilyMember

        user = db.query(User).filter(User.id == patient_id).first()
        if not user:
            return {"error": f"Patient #{patient_id} not found."}

        caretaker_phone = None
        caretaker_name = "Primary Caretaker"
        bp_limits = DEFAULT_BP_LIMITS
        hr_limits = DEFAULT_HR_LIMITS

        cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == patient_id).first()
        if cfg and cfg.is_active:
            caretaker_phone = cfg.caretaker_phone
            caretaker_name = cfg.caretaker_name or caretaker_name
            bp_limits = (cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max)
            hr_limits = (cfg.heart_rate_min, cfg.heart_rate_max)

        if not caretaker_phone:
            fm = db.query(FamilyMember).filter(FamilyMember.user_id == patient_id).first()
            if fm and (fm.phone or fm.whatsapp):
                caretaker_phone = fm.phone or fm.whatsapp
                caretaker_name = fm.full_name

        if not caretaker_phone:
            caretaker_phone = user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")

        # Get latest BP and HR readings if not explicitly provided
        sys_val = systolic
        dia_val = diastolic
        hr_val = heart_rate

        if sys_val is None or dia_val is None:
            bp_reading = (
                db.query(IoTVitalReading)
                .filter(IoTVitalReading.patient_id == patient_id, IoTVitalReading.metric_type == "blood_pressure")
                .order_by(IoTVitalReading.recorded_at.desc())
                .first()
            )
            if sys_val is None:
                sys_val = bp_reading.primary_value if bp_reading else 120.0
            if dia_val is None:
                dia_val = bp_reading.secondary_value if bp_reading else 80.0

        if hr_val is None:
            hr_reading = (
                db.query(IoTVitalReading)
                .filter(IoTVitalReading.patient_id == patient_id, IoTVitalReading.metric_type == "heart_rate")
                .order_by(IoTVitalReading.recorded_at.desc())
                .first()
            )
            hr_val = hr_reading.primary_value if hr_reading else 75.0

        return check_vitals(
            patient_id=str(patient_id),
            caretaker_phone=caretaker_phone,
            systolic_bp=float(sys_val),
            diastolic_bp=float(dia_val),
            heart_rate=float(hr_val),
            bp_limits=bp_limits,
            heart_rate_limits=hr_limits,
            patient_name=user.full_name or "Patient",
            bypass_cooldown=bypass_cooldown
        )
    finally:
        if close_db and db is not None:
            db.close()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    print("=" * 70)
    print("   CARETAKER VITAL SIGNS SMS HEALTH ALERT - TEST RUN")
    print("=" * 70)

    test_phone = os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        test_phone = sys.argv[1].strip()

    # Test Case A: Normal Vitals (No alert expected)
    print("\n1. TESTING NORMAL VITALS (BP 118/76 mmHg, HR 72 bpm):")
    res_normal = check_vitals(
        patient_id="101",
        caretaker_phone=test_phone,
        systolic_bp=118.0,
        diastolic_bp=76.0,
        heart_rate=72.0,
        patient_name="Yogesh"
    )
    print(f"   * Alert Required: {res_normal.get('alert_required')} (Expected: False)")

    # Test Case B: Abnormal Vitals (Critical Alert Expected)
    print(f"\n2. TESTING ABNORMAL VITALS (BP 168/104 mmHg, HR 118 bpm) -> Alerting {test_phone}:")
    res_abnormal = check_vitals(
        patient_id="101",
        caretaker_phone=test_phone,
        systolic_bp=168.0,
        diastolic_bp=104.0,
        heart_rate=118.0,
        patient_name="Yogesh",
        bypass_cooldown=True
    )
    print(f"   * Alert Required : {res_abnormal.get('alert_required')}")
    print(f"   * Severity       : {res_abnormal.get('severity')}")
    print(f"   * Triggered Rules: {res_abnormal.get('alerts')}")
    notification = res_abnormal.get("notification", {})
    print(f"   * SMS Status     : {notification.get('status')}")
    print(f"   * SID            : {notification.get('sid')}")
    print(f"   * Provider       : {notification.get('provider')}")
    if notification.get("error"):
        print(f"   * Error Details  : {notification.get('error')}")

    print("\n" + "=" * 70)
    print("[COMPLETE] Caretaker health alerts test execution finished.")
    print("=" * 70)
