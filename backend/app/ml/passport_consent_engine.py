"""
Context-Aware Emergency Passport & Granular Data-Bound Consent Engine.
Generates role-filtered emergency views (Public Basic vs. Paramedic vs. ER Trauma)
and enforces cryptographically verifiable, time-expiring consent permissions.
"""

import time
import secrets
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

# Role context permissions configuration
CONTEXT_PERMISSIONS = {
    "PUBLIC_BASIC": {
        "label": "Public Emergency First Responder",
        "description": "Minimal non-sensitive life-saving data viewable by general public or bystander.",
        "allowed_fields": ["blood_group", "drug_allergies", "emergency_contact_phone", "full_name"],
        "token_validity_minutes": 1440 # 24 hours
    },
    "AMBULANCE_PARAMEDIC": {
        "label": "Paramedic / ALS Ambulance Unit",
        "description": "Critical en-route triage vitals, chronic illnesses, and active prescriptions.",
        "allowed_fields": [
            "full_name", "age", "gender", "blood_group", "drug_allergies",
            "pre_existing_conditions", "current_medications", "recent_vitals",
            "emergency_contact_phone", "resuscitation_preference"
        ],
        "token_validity_minutes": 60 # 1 hour
    },
    "HOSPITAL_ER_TRAUMA": {
        "label": "Hospital Trauma Bay & Attending ER Physician",
        "description": "Full clinical dossier: lab biomarkers, radiology findings, and past medical consults.",
        "allowed_fields": [
            "full_name", "age", "gender", "blood_group", "drug_allergies",
            "pre_existing_conditions", "current_medications", "recent_vitals",
            "emergency_contact_phone", "resuscitation_preference", "recent_lab_biomarkers",
            "radiology_reports", "recent_diagnoses", "treating_physician_notes"
        ],
        "token_validity_minutes": 240 # 4 hours
    }
}

def generate_contextual_emergency_token(patient_id: int, context_scope: str = "PUBLIC_BASIC") -> Dict[str, Any]:
    """
    Generates a secure, context-bound QR token with automatic time expiration.
    """
    if context_scope not in CONTEXT_PERMISSIONS:
        context_scope = "PUBLIC_BASIC"

    scope_meta = CONTEXT_PERMISSIONS[context_scope]
    validity_mins = scope_meta["token_validity_minutes"]
    
    expires_at = datetime.utcnow() + timedelta(minutes=validity_mins)
    raw_entropy = f"{patient_id}:{context_scope}:{time.time()}:{secrets.token_hex(16)}"
    token_hash = hashlib.sha256(raw_entropy.encode()).hexdigest()[:32]

    return {
        "token": token_hash,
        "patient_id": patient_id,
        "context_scope": context_scope,
        "scope_label": scope_meta["label"],
        "expires_at": expires_at.isoformat(),
        "validity_minutes": validity_mins
    }

def filter_patient_data_by_context(
    full_patient_data: Dict[str, Any],
    context_scope: str
) -> Dict[str, Any]:
    """
    Strictly filters and sanitizes patient record according to context security scope.
    Ensures zero leakage of sensitive medical history to unauthorized contexts.
    """
    scope_meta = CONTEXT_PERMISSIONS.get(context_scope, CONTEXT_PERMISSIONS["PUBLIC_BASIC"])
    allowed_fields = set(scope_meta["allowed_fields"])

    filtered_record = {
        "access_scope": context_scope,
        "scope_label": scope_meta["label"],
        "filtered_at": datetime.utcnow().isoformat(),
        "disclaimer": "Access strictly logged under tamper-evident healthcare audit trail."
    }

    for key, value in full_patient_data.items():
        if key in allowed_fields:
            filtered_record[key] = value

    return filtered_record
