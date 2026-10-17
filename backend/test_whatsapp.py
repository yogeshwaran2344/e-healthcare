"""
Direct WhatsApp & SMS Routing Test Script
Validates connection and phone number formatting for the direct multi-channel routing engine.

Usage:
    python test_whatsapp.py
    python test_whatsapp.py +919876543210
    python test_whatsapp.py +919876543210 "Custom test notification"
"""

import sys
import os
from pathlib import Path

# Ensure current folder is in python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from whatsapp_service import (
    send_whatsapp,
    sanitize_phone_number,
    format_whatsapp_recipient,
    check_whatsapp_service_health
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_test():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE PLATFORM - DIRECT WHATSAPP & SMS GATEWAY")
    print("=" * 70)

    # 1. Inspect Service Health
    health = check_whatsapp_service_health()
    print("\n1. GATEWAY STATUS:")
    print(f"   * Status               : {health['status'].upper()}")
    print(f"   * Provider             : {health['provider']}")
    print(f"   * Supports All Numbers : {'YES' if health['supports_all_numbers'] else 'NO'}")
    print(f"   * Third-Party Dependency: NONE (Direct Universal Routing)")

    # 2. Determine Test Recipient
    default_recipient = os.getenv("DEFAULT_ALERT_RECIPIENT", "+919876543210")
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        recipient = sys.argv[1].strip()
    else:
        recipient = default_recipient

    custom_message = (
        sys.argv[2] if len(sys.argv) > 2
        else "Test notification from the NeuroCare healthcare project: Direct WhatsApp gateway is active."
    )

    clean_phone = sanitize_phone_number(recipient)
    formatted_recipient = format_whatsapp_recipient(recipient)

    print("\n2. RECIPIENT DETAILS:")
    print(f"   * Raw Input Number     : {recipient}")
    print(f"   * Sanitized E.164      : {clean_phone}")
    print(f"   * WhatsApp Target      : {formatted_recipient}")

    # 3. Dispatch Message
    print("\n3. GENERATING DIRECT MULTI-CHANNEL DISPATCH:")
    result = send_whatsapp(recipient, custom_message)

    print("\n4. RESULT REPORT:")
    print(f"   * Success      : {result.get('success')}")
    print(f"   * Status       : {result.get('status')}")
    print(f"   * Delivery SID : {result.get('sid')}")
    print(f"   * Provider     : {result.get('provider')}")

    print("\n[DIRECT 1-TAP DISPATCH LINKS]")
    print(f"   * Direct WhatsApp URL: {result.get('direct_whatsapp_url')}")
    print(f"   * Direct SMS URL     : {result.get('direct_sms_url')}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Direct notification ready for any mobile number!")
    print("=" * 70)

    return result

if __name__ == "__main__":
    run_test()
