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
    format_whatsapp_display,
    check_whatsapp_service_health
)

def check_sms_service_health() -> Dict[str, Any]:
    """Returns Fast2SMS configuration health and operational status."""
    cfg = get_fast2sms_config()
    is_ready = bool(cfg["api_key"])
    return {
        "status": "active" if is_ready else "ready_for_credentials",
        "provider": "Fast2SMS Quick SMS Gateway",
        "channel": "sms",
        "api_key_configured": is_ready,
        "route": cfg["route"],
        "default_recipient": cfg["default_recipient"],
        "supports_all_numbers": True,
        "requires_dlt": False,
        "automated": True,
        "instructions": (
            "Fast2SMS Quick Route ('q') sends cellular SMS automatically to any 10-digit Indian number "
            "with zero DLT template registration required."
        )
    }


def send_cellular_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """
    Sends an automated cellular SMS to a 10-digit Indian mobile number via Fast2SMS Quick Route ('q').
    Does not require DLT registration or entity approvals.
    """
    clean_digits = sanitize_indian_mobile_number(recipient_phone)
    if not clean_digits or len(clean_digits) != 10:
        error_msg = f"Invalid 10-digit Indian mobile number: '{recipient_phone}'"
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failed",
            "error": error_msg,
            "phone": recipient_phone,
            "channel": "sms"
        }

    cfg = get_fast2sms_config()
    api_key = cfg["api_key"]
    if not api_key:
        error_msg = "FAST2SMS_API_KEY is not configured in .env."
        logger.error(error_msg)
        return {
            "success": False,
            "status": "failed",
            "error": error_msg,
            "phone": clean_digits,
            "channel": "sms"
        }

    url = "https://www.fast2sms.com/dev/bulkV2"
    headers = {
        "authorization": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "route": route,
        "message": message.strip(),
        "numbers": clean_digits,
        "flash": 0
    }

    try:
        logger.info(f"Dispatching cellular SMS to +91{clean_digits} via Fast2SMS Route '{route}'...")
        response = requests.post(url, headers=headers, json=payload, timeout=12)
        resp_json = response.json() if response.content else {}

        if response.status_code == 200 and resp_json.get("return") is True:
            request_id = resp_json.get("request_id") or f"F2SMS-{int(time.time()*1000)}"
            logger.info(f"Cellular SMS successfully delivered! Request ID: {request_id}")
            return {
                "success": True,
                "sid": request_id,
                "status": "delivered",
                "provider": "Fast2SMS Quick SMS Gateway",
                "route": route,
                "channel": "sms",
                "phone": f"+91{clean_digits}",
                "recipient_10digit": clean_digits,
                "message": message.strip(),
                "fast2sms_response": resp_json,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        else:
            err_msg = resp_json.get("message") or f"Fast2SMS API returned status {response.status_code}"
            if isinstance(err_msg, list):
                err_msg = ", ".join(err_msg)
            logger.warning(f"Fast2SMS returned error: {err_msg}")
            
            sim_sid = f"F2SMS-ERR-{clean_digits[-4:]}"
            return {
                "success": False,
                "sid": sim_sid,
                "status": "gateway_rejected",
                "provider": "Fast2SMS Quick SMS Gateway",
                "route": route,
                "channel": "sms",
                "phone": f"+91{clean_digits}",
                "recipient_10digit": clean_digits,
                "message": message.strip(),
                "error": err_msg,
                "fast2sms_response": resp_json,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
    except Exception as e:
        logger.error(f"Network error communicating with Fast2SMS: {e}")
        return {
            "success": False,
            "status": "failed",
            "provider": "Fast2SMS Quick SMS Gateway",
            "channel": "sms",
            "error": str(e),
            "phone": f"+91{clean_digits}"
        }


def send_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """Unified SMS dispatch via Fast2SMS."""
    return send_cellular_sms(recipient_phone=recipient_phone, message=message, route=route)


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

