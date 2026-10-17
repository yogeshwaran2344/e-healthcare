"""
MSG91 Automated SMS Test Script
Tests cellular SMS transmission to any recipient mobile number using MSG91 Gateway.

Usage:
  python backend/test_sms.py
  python backend/test_sms.py +918618912755
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
for env_path in [_PROJECT_ROOT / ".env", _CURRENT_DIR / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        break
else:
    load_dotenv()

sys.path.insert(0, str(_CURRENT_DIR))
from sms_service import send_sms_msg91, sanitize_sms_recipient_digits, check_sms_service_health, get_msg91_config

def run_sms_test():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE - MSG91 AUTOMATED SMS TEST")
    print("=" * 70)

    cfg = get_msg91_config()
    health = check_sms_service_health()
    raw_phone = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")
    clean_digits = sanitize_sms_recipient_digits(raw_phone)

    print(f"\n1. TARGET RECIPIENT:")
    print(f"   * Input Number : {raw_phone}")
    print(f"   * MSG91 Format : {clean_digits}")

    print(f"\n2. MSG91 GATEWAY STATUS:")
    print(f"   * Auth Key Configured : {health['auth_key_configured']}")
    print(f"   * Sender ID           : {cfg['sender_id']}")
    print(f"   * Flow ID Default     : {cfg['flow_id_default'] or '[Not set]'}")

    if not cfg["auth_key"]:
        print("\n" + "!" * 70)
        print("   NOTE: MSG91_AUTH_KEY is not yet entered in .env.")
        print("   To send real cellular SMS automatically to phones:")
        print("   1. Open: https://msg91.com/ and sign in")
        print("   2. Copy your AuthKey into MSG91_AUTH_KEY in .env")
        print("   3. Configure your approved Sender ID and Flow ID in .env")
        print("!" * 70)

    test_message = (
        f"NeuroCare Health Alert: Test SMS verification successful for patient monitoring. "
        f"Medication reminders and caretaker alerts are active."
    )

    print(f"\n3. DISPATCHING AUTOMATED SMS TO +{clean_digits}...")
    res = send_sms_msg91(
        recipient_phone=clean_digits,
        message=test_message,
        template_variables={"patient_name": "Patient", "message": test_message}
    )

    print("\n4. DISPATCH REPORT:")
    print(f"   * Success  : {res.get('success')}")
    print(f"   * Status   : {res.get('status')}")
    print(f"   * SID / ID : {res.get('sid')}")
    print(f"   * Provider : {res.get('provider')}")

    if res.get("response"):
        print(f"   * Gateway Response : {res.get('response')}")

    print("=" * 70)
    print("[COMPLETE] SMS dispatch execution finished.")
    print("=" * 70)

if __name__ == "__main__":
    run_sms_test()
