"""
Backend App SMS Service Bridge
Exposes Fast2SMS Quick Route SMS capabilities from backend.sms_service
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from sms_service import (
    send_sms,
    send_cellular_sms,
    send_sms_msg91,
    sanitize_indian_mobile_number,
    sanitize_sms_recipient_digits,
    sanitize_phone_number,
    get_fast2sms_config,
    get_msg91_config,
    check_sms_service_health,
    is_sms_enabled,
    set_sms_enabled
)

__all__ = [
    "send_sms",
    "send_cellular_sms",
    "send_sms_msg91",
    "sanitize_indian_mobile_number",
    "sanitize_sms_recipient_digits",
    "sanitize_phone_number",
    "get_fast2sms_config",
    "get_msg91_config",
    "check_sms_service_health",
    "is_sms_enabled",
    "set_sms_enabled"
]
