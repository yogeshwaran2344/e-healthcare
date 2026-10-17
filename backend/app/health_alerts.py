"""
Backend App Health Alerts Bridge
"""

import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from health_alerts import (
    check_vitals,
    validate_vital_reading,
    evaluate_patient_latest_vitals,
    DEFAULT_BP_LIMITS,
    DEFAULT_HR_LIMITS
)

__all__ = [
    "check_vitals",
    "validate_vital_reading",
    "evaluate_patient_latest_vitals",
    "DEFAULT_BP_LIMITS",
    "DEFAULT_HR_LIMITS"
]
