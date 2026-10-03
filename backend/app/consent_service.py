"""
Patient-Controlled Consent & Backend Authorization Enforcement Service
======================================================================
Enforces granular, category-specific patient consent on the backend API layer.
Categories supported:
- diagnoses: consultation records, predicted diseases, SBAR handovers
- prescriptions: prescribed medicines, dosages, durations
- labs: diagnostic reports, biomarker findings, radiology scans
- vitals: live wearable IoT streams, blood pressure, glucose, heart rate
- mental_health: psychotherapy and psychiatric evaluations
- genetic: genomic sequencing and DNA panel data

Enforces the Separately Defined Emergency-Access Policy:
- If an active Emergency Break-Glass Override or Active SOS dispatch exists for the patient,
  emergency clinical access is permitted and immediately audited in EmergencyAccessAudit.
- Otherwise, a doctor must have an active, non-expired ConsentRecord granted by the patient
  covering the requested category.
- Frontends cannot bypass this check; enforcement is strictly server-side.
"""
import json
from datetime import datetime
from typing import Tuple, Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from .models import User, ConsentRecord, EmergencyAlert, BlockchainBlock
from .emergency_passport_service import record_emergency_access

VALID_CONSENT_CATEGORIES = {
    "diagnoses",
    "prescriptions",
    "labs",
    "vitals",
    "mental_health",
    "genetic"
}

def parse_permissions(perm_field: Any) -> List[str]:
    if isinstance(perm_field, list):
        return [str(p).lower() for p in perm_field]
    if isinstance(perm_field, str):
        try:
            parsed = json.loads(perm_field)
            if isinstance(parsed, list):
                return [str(p).lower() for p in parsed]
        except Exception:
            pass
        return [p.strip().lower() for p in perm_field.split(",") if p.strip()]
    return []

def is_emergency_override_active(
    db: Session,
    patient_id: int,
    doctor_id: int,
    max_window_hours: int = 2
) -> Tuple[bool, Optional[str]]:
    """
    Checks if an emergency break-glass override was executed within the active window (default 2 hours).
    """
    # 1. Check recent break-glass blocks on the blockchain
    recent_blocks = (
        db.query(BlockchainBlock)
        .filter(
            BlockchainBlock.patient_id == patient_id,
            BlockchainBlock.record_type == "BREAK_GLASS_OVERRIDE"
        )
        .order_by(BlockchainBlock.timestamp.desc())
        .limit(5)
        .all()
    )
    now = datetime.utcnow()
    for b in recent_blocks:
        if b.timestamp:
            elapsed_seconds = (now - b.timestamp).total_seconds()
            if elapsed_seconds <= (max_window_hours * 3600):
                return True, f"Active Emergency Break-Glass Override (Block #{b.block_index})"

    # 2. Check active EmergencyAlerts (e.g. 1-Tap SOS in transit)
    active_alert = (
        db.query(EmergencyAlert)
        .filter(
            EmergencyAlert.patient_id == patient_id,
            EmergencyAlert.status.in_(["dispatched", "arrived", "en_route"])
        )
        .order_by(EmergencyAlert.created_at.desc())
        .first()
    )
    if active_alert:
        return True, f"Active 1-Tap SOS Trauma Alert #{active_alert.id}"

    return False, None

def check_patient_consent(
    db: Session,
    patient_id: int,
    accessor: User,
    category: str
) -> Tuple[bool, str, Optional[int]]:
    """
    Evaluates whether the accessor is authorized to access data under `category`.
    Returns: (is_authorized, reason_string, consent_id)
    """
    # 1. Patients have sovereign access to their own records
    if accessor.id == patient_id:
        return True, "Patient self-access", None

    # 2. System administrators can access non-clinical metadata but clinical categories require audit
    if accessor.role == "admin":
        return True, "Administrative audit role", None

    # 3. Healthcare Professionals (Doctors)
    if accessor.role == "doctor":
        # A. Check Emergency Override Policy
        is_em, em_reason = is_emergency_override_active(db, patient_id, accessor.id)
        if is_em:
            return True, em_reason or "Emergency clinical override", None

        # B. Check Active Consent Records
        now = datetime.utcnow()
        consents = (
            db.query(ConsentRecord)
            .filter(
                ConsentRecord.patient_id == patient_id,
                ConsentRecord.status == "active"
            )
            .order_by(ConsentRecord.created_at.desc())
            .all()
        )

        for c in consents:
            # Check expiry
            if c.expires_at and c.expires_at < now:
                c.status = "expired"
                db.commit()
                continue

            # Check if this consent matches this doctor or hospital
            grantee_name_lower = (c.grantee_name or "").lower()
            accessor_name_lower = (accessor.full_name or "").lower()

            matches_doctor = False
            if (
                accessor_name_lower in grantee_name_lower
                or grantee_name_lower in accessor_name_lower
                or c.grantee_type in ["doctor", "all_doctors", "clinic", "hospital"]
            ):
                matches_doctor = True

            if matches_doctor:
                allowed_categories = parse_permissions(c.permissions)
                if category.lower() in allowed_categories or "all" in allowed_categories:
                    return True, f"Authorized under Consent Grant #{c.id} ({c.grantee_name})", c.id

        return False, f"No active patient consent granted for category '{category}'", None

    return False, "Unauthorized accessor role", None

def enforce_patient_consent_or_emergency(
    db: Session,
    patient_id: int,
    accessor: User,
    category: str,
    purpose: Optional[str] = None
) -> None:
    """
    Raises HTTP 403 Forbidden if consent is missing.
    Automatically generates an audit record on every evaluation.
    """
    authorized, reason, consent_id = check_patient_consent(db, patient_id, accessor, category)

    is_emergency = "Emergency" in reason or "SOS" in reason or "Break-Glass" in reason
    
    # Record access attempt in audit log
    record_emergency_access(
        db,
        accessor=accessor,
        patient_id=patient_id,
        purpose=purpose or reason,
        information_type=f"category:{category}",
        is_emergency=is_emergency,
        access_channel="api_consent_gated",
        context_scope=f"CONSENT_ID_{consent_id}" if consent_id else ("EMERGENCY" if is_emergency else "DENIED" if not authorized else "SELF")
    )

    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Access denied: Patient has not granted active consent for medical category '{category}'. "
                "Request patient consent through the portal or execute an Emergency Break-Glass override in acute trauma scenarios."
            )
        )
