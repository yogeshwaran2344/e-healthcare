"""
Backend App WhatsApp Service Bridge
Exposes WhatsApp notification capabilities from backend.whatsapp_service
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
    format_whatsapp_recipient,
    check_whatsapp_service_health,
    DEFAULT_SANDBOX_FROM
)

__all__ = [
    "send_whatsapp",
    "sanitize_phone_number",
    "format_whatsapp_recipient",
    "check_whatsapp_service_health",
    "DEFAULT_SANDBOX_FROM"
]
