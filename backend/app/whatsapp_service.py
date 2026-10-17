"""
Backend App WhatsApp Service Bridge
Exposes Meta WhatsApp Cloud API capabilities from backend.whatsapp_service
"""

import sys
from pathlib import Path

# Ensure backend root is in sys.path
_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from whatsapp_service import (
    send_whatsapp,
    sanitize_phone_number,
    sanitize_meta_recipient_digits,
    format_whatsapp_recipient,
    format_whatsapp_direct_url,
    format_sms_direct_url,
    send_meta_whatsapp_cloud_api,
    get_meta_cloud_config,
    check_whatsapp_service_health,
    DEFAULT_SANDBOX_FROM
)

__all__ = [
    "send_whatsapp",
    "sanitize_phone_number",
    "sanitize_meta_recipient_digits",
    "format_whatsapp_recipient",
    "format_whatsapp_direct_url",
    "format_sms_direct_url",
    "send_meta_whatsapp_cloud_api",
    "get_meta_cloud_config",
    "check_whatsapp_service_health",
    "DEFAULT_SANDBOX_FROM"
]
