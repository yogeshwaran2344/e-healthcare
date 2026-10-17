"""
Backend App WhatsApp Service Bridge
Exposes automated WhatsApp notification capabilities from backend.whatsapp_service
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from whatsapp_service import (
    send_whatsapp,
    send_sms,
    send_sms_msg91,
    sanitize_indian_mobile_number,
    sanitize_sms_recipient_digits,
    sanitize_phone_number,
    format_whatsapp_recipient,
    format_whatsapp_display,
    format_whatsapp_url,
    format_whatsapp_api_url,
    get_whatsapp_config,
    get_fast2sms_config,
    get_msg91_config,
    check_whatsapp_service_health,
    check_sms_service_health
)

__all__ = [
    "send_whatsapp",
    "send_sms",
    "send_sms_msg91",
    "sanitize_indian_mobile_number",
    "sanitize_sms_recipient_digits",
    "sanitize_phone_number",
    "format_whatsapp_recipient",
    "format_whatsapp_display",
    "format_whatsapp_url",
    "format_whatsapp_api_url",
    "get_whatsapp_config",
    "get_fast2sms_config",
    "get_msg91_config",
    "check_whatsapp_service_health",
    "check_sms_service_health"
]
