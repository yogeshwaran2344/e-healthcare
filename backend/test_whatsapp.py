"""
Twilio WhatsApp Messaging Test Script
Validates connection to the Twilio WhatsApp API / Sandbox, tests phone number formatting,
and reports transmission status.

Usage:
    python test_whatsapp.py
    python test_whatsapp.py +918618912755
    python test_whatsapp.py +918618912755 "Custom test message"
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
    check_whatsapp_service_health,
    get_twilio_credentials
)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

def run_test():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE PLATFORM - TWILIO WHATSAPP GATEWAY TEST")
    print("=" * 70)

    # 1. Inspect Service Health & Configuration
    health = check_whatsapp_service_health()
    sid, token, sender = get_twilio_credentials()
    
    print("\n1. CONFIGURATION CHECK:")
    print(f"   * Account SID Configured: {'YES' if health['has_account_sid'] else 'NO (placeholder or missing)'}")
    print(f"   * Auth Token Configured : {'YES' if health['has_auth_token'] else 'NO (placeholder or missing)'}")
    print(f"   * WhatsApp Sender       : {sender}")
    print(f"   * Using Sandbox Number  : {'YES' if health['is_sandbox'] else 'NO'}")

    # 2. Determine Test Recipient
    default_recipient = os.getenv("TWILIO_DEFAULT_RECIPIENT", "+918618912755")
    if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        recipient = sys.argv[1].strip()
    else:
        recipient = default_recipient

    custom_message = (
        sys.argv[2] if len(sys.argv) > 2
        else "Test notification from the NeuroCare healthcare project: WhatsApp gateway is active."
    )

    formatted_recipient = format_whatsapp_recipient(recipient)
    print("\n2. RECIPIENT DETAILS:")
    print(f"   * Raw Input Number     : {recipient}")
    print(f"   * Sanitized E.164      : {sanitize_phone_number(recipient)}")
    print(f"   * Twilio Target Format : {formatted_recipient}")

    # 3. Dispatch Test Message
    print("\n3. DISPATCHING TEST WHATSAPP MESSAGE:")
    print(f"   Sending to {formatted_recipient}...")
    result = send_whatsapp(recipient, custom_message)

    print("\n4. RESULT REPORT:")
    print(f"   * Success : {result.get('success')}")
    print(f"   * Status  : {result.get('status')}")
    print(f"   * SID     : {result.get('sid')}")
    
    if result.get("error"):
        print(f"   * Error   : {result.get('error')}")
    if result.get("help_tip"):
        print(f"\n[DIAGNOSTIC GUIDANCE]")
        print(f"   {result.get('help_tip')}")

    if result.get("direct_whatsapp_url"):
        print(f"\n[MULTI-CHANNEL ROUTING LINKS FOR ANY MOBILE NUMBER]")
        print(f"   * Direct WhatsApp URL: {result.get('direct_whatsapp_url')}")
        print(f"   * Direct SMS URL     : {result.get('direct_sms_url')}")

    print("\n" + "=" * 70)
    if result.get("success"):
        print("[SUCCESS] WhatsApp test message transmitted successfully via Twilio API!")
    elif result.get("simulated"):
        print("[SIMULATED] Twilio credentials missing; click the Direct WhatsApp URL above to dispatch.")
    else:
        print("[DIRECT ROUTING READY] Click the Direct WhatsApp URL above to dispatch to any number instantly,")
        print("                        or check Twilio Sandbox enrollment for direct API delivery.")
    print("=" * 70)

    return result

if __name__ == "__main__":
    run_test()

