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
    """Compatibility health check: returns automated WhatsApp gateway status."""
    return check_whatsapp_service_health()


def send_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """
    Unified notification dispatch: delivers exclusively via automated WhatsApp gateway.
    SMS delivery has been completely disabled as per user instruction.
    """
    return send_whatsapp(recipient_phone=recipient_phone, message=message)


def send_cellular_sms(
    recipient_phone: str,
    message: str,
    route: str = "q"
) -> Dict[str, Any]:
    """
    Redirects legacy cellular SMS requests directly to automated WhatsApp dispatch.
    Physical cellular SMS transmission is disabled.
    """
    return send_whatsapp(recipient_phone=recipient_phone, message=message)


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

