"""
Fast2SMS Automated Cellular SMS Test Script
Tests cellular SMS transmission to any recipient mobile number using Fast2SMS Quick Route ('q').

Usage:
  python backend/test_sms.py
  python backend/test_sms.py 8618912755
  python backend/test_sms.py +918618912755
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
for env_path in [_PROJECT_ROOT / ".env", _CURRENT_DIR / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        break
else:
    load_dotenv()

sys.path.insert(0, str(_CURRENT_DIR))
from sms_service import (
    send_sms,
    sanitize_indian_mobile_number,
    check_sms_service_health,
    get_fast2sms_config
)

def run_sms_test():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE - FAST2SMS CELLULAR SMS TEST")
    print("=" * 70)

    cfg = get_fast2sms_config()
    health = check_sms_service_health()
    raw_phone = sys.argv[1] if len(sys.argv) > 1 else os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")
    clean_digits = sanitize_indian_mobile_number(raw_phone)

    print(f"\n1. TARGET RECIPIENT:")
    print(f"   * Input Number       : {raw_phone}")
    print(f"   * 10-Digit Cleaned   : {clean_digits}")
    print(f"   * Full Carrier Format: +91 {clean_digits}")

    print(f"\n2. FAST2SMS GATEWAY STATUS:")
    print(f"   * API Key Configured : {health['api_key_configured']}")
    print(f"   * Route              : {cfg['route']} (Quick SMS - No DLT Needed)")
    print(f"   * Requires DLT       : False")
    print(f"   * Automated Delivery : True")

    if not cfg["api_key"]:
        print("\n" + "!" * 70)
        print("   NOTE: FAST2SMS_API_KEY is not yet entered in .env.")
        print("   To send real cellular SMS automatically to phones:")
        print("   1. Open https://www.fast2sms.com/ and create a free account")
        print("   2. Open 'Dev API' in your Fast2SMS dashboard and copy your API Key")
        print("   3. Add FAST2SMS_API_KEY=your_key in your .env file")
        print("!" * 70)

    test_message = (
        f"NeuroCare Health Alert: Test SMS verification successful for patient monitoring. "
        f"Medication reminders and caretaker alerts are active."
    )

    print(f"\n3. DISPATCHING CELLULAR SMS TO +91{clean_digits}...")
    res = send_sms(
        recipient_phone=clean_digits,
        message=test_message
    )

    print("\n4. DISPATCH REPORT:")
    print(f"   * Success   : {res.get('success')}")
    print(f"   * Status    : {res.get('status')}")
    print(f"   * SID / ID  : {res.get('sid')}")
    print(f"   * Provider  : {res.get('provider')}")
    print(f"   * Recipient : {res.get('phone')}")
    if res.get("error"):
        print(f"   * Notice/Error : {res.get('error')}")
    if res.get("notice"):
        print(f"   * Info         : {res.get('notice')}")
    if res.get("gateway_response"):
        print(f"   * Gateway Data : {res.get('gateway_response')}")

    print("=" * 70)
    print("[COMPLETE] Fast2SMS dispatch execution finished.")
    print("=" * 70)

if __name__ == "__main__":
    run_sms_test()
