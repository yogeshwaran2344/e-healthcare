"""
Backend App Medication Reminders Bridge
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from medication_reminders import (
    send_medication_reminder,
    check_and_send_due_reminders,
    start_medication_scheduler,
    stop_medication_scheduler
)

__all__ = [
    "send_medication_reminder",
    "check_and_send_due_reminders",
    "start_medication_scheduler",
    "stop_medication_scheduler"
]
