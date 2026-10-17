"""
NeuroCare Automated WhatsApp Gateway Verification Script
Tests automated WhatsApp message delivery for:
1. Direct test WhatsApp verification
2. Patient medication reminder dispatch via WhatsApp
3. Caretaker vital signs anomaly alert dispatch via WhatsApp (Blood Pressure & Heart Rate)
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from whatsapp_service import (
    send_whatsapp,
    sanitize_indian_mobile_number,
    format_whatsapp_recipient,
    format_whatsapp_display,
    format_whatsapp_url,
    check_whatsapp_service_health,
    get_whatsapp_config
)
from medication_reminders import send_medication_reminder
from health_alerts import check_vitals

def run_whatsapp_verification():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE - AUTOMATED WHATSAPP NOTIFICATION SUITE")
    print("=" * 70)

    cfg = get_whatsapp_config()
    health = check_whatsapp_service_health()
    target_phone = sys.argv[1] if len(sys.argv) > 1 else cfg["default_recipient"]
    clean_digits = sanitize_indian_mobile_number(target_phone)

    print(f"\n1. GATEWAY HEALTH & CONFIGURATION:")
    print(f"   * Channel            : {health['channel'].upper()}")
    print(f"   * Active Provider    : {health['provider']}")
    print(f"   * Status             : {health['status'].upper()}")
    print(f"   * Target Recipient   : {format_whatsapp_display(target_phone)} (digits: {format_whatsapp_recipient(target_phone)})")
    print(f"   * Automated Dispatch : {health['automated']}")

    print(f"\n2. DISPATCHING VERIFICATION TEST WHATSAPP MESSAGE:")
    test_msg = (
        "NeuroCare Healthcare Platform: Automated WhatsApp notification channel verified. "
        "Real-time medication reminders & caretaker vitals alerts active."
    )
    res1 = send_whatsapp(target_phone, test_msg)
    print(f"   * Delivery Status    : {res1.get('status')}")
    print(f"   * Message SID/WAMID  : {res1.get('sid')}")
    print(f"   * Direct Link        : {res1.get('direct_whatsapp_url')}")
    assert res1.get("success") is True, "Direct WhatsApp test failed!"

    print(f"\n3. DISPATCHING WORKFLOW 1 - PATIENT MEDICATION REMINDER:")
    res2 = send_medication_reminder(
        patient_phone=clean_digits,
        medication_name="Metformin 500mg",
        scheduled_time="08:00 AM",
        dosage="1 tablet",
        patient_name="John Doe"
    )
    print(f"   * Medication         : {res2.get('medication_name')}")
    print(f"   * Dose Due           : {res2.get('scheduled_time')}")
    print(f"   * Channel            : {res2.get('channel')}")
    print(f"   * Delivery Status    : {res2.get('status')}")
    print(f"   * Message Text       : {res2.get('message')}")
    assert res2.get("success") is True, "Medication reminder failed!"

    print(f"\n4. DISPATCHING WORKFLOW 2 - ABNORMAL VITALS CARETAKER ALERT:")
    caretaker_target = cfg.get("caretaker_phone", target_phone)
    res3 = check_vitals(
        patient_id="PT-1001",
        caretaker_phone=caretaker_target,
        systolic_bp=168.0,
        diastolic_bp=104.0,
        heart_rate=122.0,
        patient_name="John Doe",
        bypass_cooldown=True
    )
    print(f"   * Alert Required     : {res3.get('alert_required')}")
    print(f"   * Severity Tier      : {res3.get('severity')}")
    print(f"   * Channel            : {res3.get('channel')}")
    print(f"   * Triggered Triggers : {res3.get('alerts')}")
    print(f"   * Message Text       : {res3.get('message')}")
    print(f"   * Caretaker Phone    : +91 {sanitize_indian_mobile_number(caretaker_target)}")
    notif = res3.get("notification", {})
    print(f"   * Caretaker Status   : {notif.get('status')} (SID: {notif.get('sid')})")
    assert res3.get("alert_required") is True, "Caretaker alert should be required!"
    assert notif.get("success") is True, "Caretaker notification failed!"

    print(f"\n5. TESTING NORMAL VITALS (NO FALSE POSITIVES):")
    res4 = check_vitals(
        patient_id="PT-1001",
        caretaker_phone=caretaker_target,
        systolic_bp=120.0,
        diastolic_bp=80.0,
        heart_rate=72.0,
        patient_name="John Doe",
        bypass_cooldown=True
    )
    print(f"   * Alert Required     : {res4.get('alert_required')} (Expected: False)")
    assert res4.get("alert_required") is False, "Normal vitals should not trigger alert!"

    print("\n" + "=" * 70)
    print("   ALL AUTOMATED WHATSAPP VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_whatsapp_verification()
