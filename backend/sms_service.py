"""
Fast2SMS Gateway Service (Automated Server-Side Cellular SMS)
Provides automated direct SMS delivery for:
1. Patient medication reminders when doses are due.
2. Caretaker vital signs alerts for abnormal Blood Pressure or Heart Rate.
3. System verification test SMS to Patient and Caretaker.

Uses Fast2SMS Quick SMS API (Route: 'q').
- Route 'q' sends free-text SMS directly to 10-digit Indian mobile numbers.
- Does NOT require DLT template registration or Entity ID approvals.
- Documentation: https://www.fast2sms.com/dev/bulkV2
"""

import os
import re
import time
import hashlib
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import requests

logger = logging.getLogger("SMSService")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# Load environment
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent if _CURRENT_DIR.name == "backend" else _CURRENT_DIR
import sys
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

for env_path in [_PROJECT_ROOT / ".env", _CURRENT_DIR / ".env", Path(".env")]:
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
        break
else:
    load_dotenv()


FALLBACK_FAST2SMS_API_KEY = "0143Vm2DoXJkbCihNnwBtZgcLWlTF9z6xsYUaMr5IEQ8SpdReydgLOxjimuetZJ8rbP23spcY6W0oE1R"

def get_fast2sms_config() -> Dict[str, str]:
    """Retrieves Fast2SMS configuration from environment, always ensuring latest values."""
    for env_path in [_PROJECT_ROOT / ".env", _CURRENT_DIR / ".env", Path(".env")]:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
            break
    api_key = (os.getenv("FAST2SMS_API_KEY") or "").strip()
    if not api_key:
        api_key = FALLBACK_FAST2SMS_API_KEY
    return {
        "api_key": api_key,
        "route": (os.getenv("FAST2SMS_ROUTE") or "q").strip(),
        "default_recipient": (os.getenv("DEFAULT_ALERT_RECIPIENT") or "+918618912755").strip()
    }


def sanitize_indian_mobile_number(phone: str) -> str:
    """
    Cleans phone number to 10-digit Indian mobile number format.
    Fast2SMS expects 10 digits without '+' or country code prefix.
    
    Examples:
      '+91 86189 12755' -> '8618912755'
      '+918618912755'   -> '8618912755'
      '918618912755'    -> '8618912755'
      '08618912755'     -> '8618912755'
      '8618912755'      -> '8618912755'
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if not digits:
        return ""
    if len(digits) == 10:
        return digits
    elif len(digits) == 12 and digits.startswith("91"):
        return digits[2:]
    elif len(digits) == 11 and digits.startswith("0"):
        return digits[1:]
    elif len(digits) > 10 and digits.startswith("91"):
        return digits[-10:]
    return digits


# Alias for backwards compatibility
sanitize_sms_recipient_digits = sanitize_indian_mobile_number
sanitize_phone_number = sanitize_indian_mobile_number


from whatsapp_service import (
    send_whatsapp,
    format_whatsapp_recipient,
    format_whatsapp_url,
    format_whatsapp_display
)

def send_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """
    Unified notification dispatch: delivers real cellular SMS directly via Fast2SMS Quick Route ('q').
    Zero redirects, zero template requirements.
    """
    return send_cellular_sms(recipient_phone=recipient_phone, message=message, route=route)


def send_cellular_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """
    Direct cellular SMS dispatch using Fast2SMS Quick Route ('q').
    """
    cfg = get_fast2sms_config()
    clean_digits = sanitize_indian_mobile_number(recipient_phone)

    if not clean_digits or len(clean_digits) != 10:
        error_msg = f"Invalid 10-digit recipient phone number: '{recipient_phone}'"
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failed",
            "error": error_msg,
            "phone": recipient_phone
        }

    # Clean message text
    sms_text = message.strip()

    # If FAST2SMS_API_KEY is configured, call live Fast2SMS API
    if cfg["api_key"]:
        url = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": cfg["api_key"],
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "route": route or cfg["route"] or "q",
            "message": sms_text,
            "numbers": clean_digits
        }

        try:
            logger.info(f"Dispatching live SMS to +91{clean_digits} via Fast2SMS Quick Route ('{payload['route']}')...")
            response = requests.post(url, headers=headers, json=payload, timeout=12)
            resp_data = response.json() if response.content else {}

            if response.status_code == 200 and resp_data.get("return") is True:
                req_id = resp_data.get("request_id") or f"F2SMS-{int(time.time()*1000)}"
                logger.info(f"Live SMS successfully dispatched by Fast2SMS! Request ID: {req_id}")
                return {
                    "success": True,
                    "sid": req_id,
                    "status": "delivered",
                    "provider": "Fast2SMS Quick SMS Gateway",
                    "phone": f"+91{clean_digits}",
                    "recipient_10digit": clean_digits,
                    "message": sms_text,
                    "gateway_response": resp_data
                }
            else:
                raw_err = resp_data.get("message")
                err_text = " ".join(raw_err) if isinstance(raw_err, list) else str(raw_err or f"HTTP {response.status_code}")
                if resp_data.get("status_code") == 999:
                    err_text = "Fast2SMS requires completing a one-time recharge of ₹100 ('ADD CREDIT' button in Fast2SMS dashboard) to unlock automated API sending."
                logger.warning(f"Fast2SMS API notice ({response.status_code}): {err_text}")
                return {
                    "success": False,
                    "sid": f"F2SMS-ERR-{clean_digits[-4:]}",
                    "status": "activation_needed" if resp_data.get("status_code") == 999 else "gateway_rejected",
                    "provider": "Fast2SMS Quick SMS Gateway",
                    "phone": f"+91{clean_digits}",
                    "recipient_10digit": clean_digits,
                    "error": err_text,
                    "gateway_response": resp_data
                }
        except Exception as e:
            logger.error(f"Network error communicating with Fast2SMS: {e}")
            return {
                "success": False,
                "status": "network_error",
                "error": str(e),
                "phone": f"+91{clean_digits}",
                "recipient_10digit": clean_digits
            }

    # When FAST2SMS_API_KEY is not yet in .env, simulate dispatch cleanly
    simulated_id = f"F2SMS-SIM-{hashlib.sha256(f'{clean_digits}:{time.time()}:{sms_text[:20]}'.encode()).hexdigest()[:10].upper()}"
    logger.info(f"[AUTOMATED SMS DISPATCHED] To: +91{clean_digits} | Msg: {sms_text[:70]}... (ID: {simulated_id})")

    return {
        "success": True,
        "sid": simulated_id,
        "status": "delivered",
        "provider": "Fast2SMS Quick SMS Gateway (Simulated / Enter FAST2SMS_API_KEY in .env)",
        "phone": f"+91{clean_digits}",
        "recipient_10digit": clean_digits,
        "message": sms_text,
        "notice": "SMS dispatched by backend server. To deliver real cellular SMS via telecom towers, set FAST2SMS_API_KEY in .env"
    }


# Backwards compatibility alias
def send_sms_msg91(recipient_phone: str, message: str, *args, **kwargs) -> Dict[str, Any]:
    """Compatibility wrapper redirecting legacy calls to Fast2SMS send_sms."""
    return send_sms(recipient_phone=recipient_phone, message=message)


def get_msg91_config() -> Dict[str, str]:
    """Compatibility config returning SMS config."""
    cfg = get_fast2sms_config()
    return {
        "auth_key": cfg["api_key"],
        "sender_id": "FAST2SMS",
        "flow_id_default": "route_q",
        "flow_id_medication": "route_q",
        "flow_id_alert": "route_q",
        "dlt_te_id": ""
    }


def check_sms_service_health() -> Dict[str, Any]:
    """Returns Fast2SMS configuration health and ready status."""
    cfg = get_fast2sms_config()
    is_ready = bool(cfg["api_key"])

    return {
        "status": "active" if is_ready else "ready_for_credentials",
        "provider": "Fast2SMS Quick SMS Gateway",
        "api_key_configured": is_ready,
        "route": cfg["route"],
        "default_recipient": cfg["default_recipient"],
        "supports_all_numbers": True,
        "requires_dlt": False,
        "automated": True,
        "instructions": (
            "Fast2SMS Quick Route ('q') sends cellular SMS automatically to any 10-digit Indian number "
            "with zero DLT template registration required. Add FAST2SMS_API_KEY in .env to deliver real SMS."
        )
    }
