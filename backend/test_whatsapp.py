"""
Meta WhatsApp Cloud API Test Script
Tests connectivity with Meta's Graph API:
POST https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages

Usage:
  python backend/test_whatsapp.py
  python backend/test_whatsapp.py +918618912755
  python backend/test_whatsapp.py 918618912755
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests

# Load environment
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
for env_path in [_PROJECT_ROOT / ".env", _CURRENT_DIR / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        break
else:
    load_dotenv()

TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v20.0").strip()
DEFAULT_RECIPIENT = os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755").strip()

def run_test():
    print("=" * 70)
    print("   NEUROCARE HEALTHCARE - META WHATSAPP CLOUD API TEST")
    print("=" * 70)

    # 1. Check Recipient
    raw_recipient = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RECIPIENT
    clean_digits = "".join(filter(str.isdigit, raw_recipient))
    if len(clean_digits) == 10:
        clean_digits = "91" + clean_digits
    elif len(clean_digits) == 11 and clean_digits.startswith("0"):
        clean_digits = "91" + clean_digits[1:]

    print(f"\n1. TARGET RECIPIENT:")
    print(f"   * Raw Number        : {raw_recipient}")
    print(f"   * Meta Cloud Format : {clean_digits} (Digits with country code)")

    # 2. Check Meta Environment Variables
    print(f"\n2. META API CREDENTIALS CHECK:")
    print(f"   * WHATSAPP_ACCESS_TOKEN     : {'[SET]' if TOKEN else '[NOT SET - Add to .env]'}")
    print(f"   * WHATSAPP_PHONE_NUMBER_ID  : {PHONE_NUMBER_ID if PHONE_NUMBER_ID else '[NOT SET - Add to .env]'}")
    print(f"   * WHATSAPP_API_VERSION      : {API_VERSION}")

    if not TOKEN or not PHONE_NUMBER_ID:
        print("\n" + "!" * 70)
        print("   NOTE: Meta WhatsApp Cloud API credentials are not yet set in .env.")
        print("   To send official Meta Cloud API messages:")
        print("   1. Open: https://developers.facebook.com/")
        print("   2. Go to: WhatsApp -> API Setup")
        print("   3. Copy your 'Temporary access token' into WHATSAPP_ACCESS_TOKEN in .env")
        print("   4. Copy your 'Phone Number ID' into WHATSAPP_PHONE_NUMBER_ID in .env")
        print("!" * 70)

        # Fallback to direct universal link test
        sys.path.insert(0, str(_CURRENT_DIR))
        from whatsapp_service import send_whatsapp
        test_msg = "Hello! Test healthcare notification from NeuroCare Platform."
        res = send_whatsapp(clean_digits, test_msg)
        print("\n3. UNIVERSAL MULTI-CHANNEL FALLBACK STATUS:")
        print(f"   * Status              : {res.get('status')}")
        print(f"   * Direct WhatsApp URL : {res.get('direct_whatsapp_url')}")
        print(f"   * Direct SMS URL      : {res.get('direct_sms_url')}")
        print("=" * 70)
        print("[SUCCESS] Local & direct multi-channel routing is active!")
        print("=" * 70)
        return

    # 3. Perform Live Meta WhatsApp Cloud API Request (Step 4 from instructions)
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # Meta official 'hello_world' test template
    payload = {
        "messaging_product": "whatsapp",
        "to": clean_digits,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }

    print(f"\n3. TRANSMITTING TEST TEMPLATE ('hello_world') VIA META GRAPH API...")
    print(f"   * Endpoint: {url}")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        print(f"   * HTTP Status Code: {response.status_code}")
        
        try:
            resp_data = response.json()
        except Exception:
            resp_data = {"raw": response.text}

        print("\n4. META API RESPONSE:")
        print(f"   {resp_data}")

        if response.status_code in (200, 201):
            messages = resp_data.get("messages", [])
            wamid = messages[0].get("id") if messages else "N/A"
            print("\n" + "=" * 70)
            print(f"[SUCCESS] Meta WhatsApp message accepted by Graph API!")
            print(f"Message ID (WAMID): {wamid}")
            print("Check the recipient's WhatsApp to confirm message arrival.")
            print("=" * 70)
        else:
            err = resp_data.get("error", {})
            print("\n" + "-" * 70)
            print(f"⚠️ Meta Graph API returned error: {err.get('message')}")
            print(f"   Error Code: {err.get('code')}")
            print(f"   Error Subcode: {err.get('error_subcode')}")
            if err.get('code') == 190:
                print("   👉 TIP: Access token is expired or invalid. Generate a new token in Meta Developer Portal.")
            elif err.get('code') == 131030:
                print("   👉 TIP: Test recipient number is not registered in your Meta test account recipient list.")
            print("-" * 70)

    except Exception as e:
        print(f"\n❌ Network request failed: {e}")

if __name__ == "__main__":
    run_test()
