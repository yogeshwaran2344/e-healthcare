"""Shared live emergency passport assembly and access auditing."""
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from .models import (
    User,
    DoctorProfile,
    Consultation,
    Prescription,
    IoTVitalReading,
    EmergencyAccessAudit,
)
from .ml.emergency_engine import assemble_live_emergency_passport


def fetch_latest_vitals(db: Session, patient_id: int) -> Dict[str, Any]:
    latest_rows = (
        db.query(IoTVitalReading)
        .filter(IoTVitalReading.patient_id == patient_id)
        .order_by(IoTVitalReading.recorded_at.desc())
        .limit(12)
        .all()
    )
    vitals: Dict[str, Any] = {}
    for r in latest_rows:
        if r.metric_type in vitals:
            continue
        if r.metric_type == "blood_pressure":
            vitals["blood_pressure"] = f"{int(r.primary_value)}/{int(r.secondary_value or 80)} mmHg"
        elif r.metric_type == "glucose":
            vitals["glucose"] = f"{int(r.primary_value)} mg/dL"
        elif r.metric_type == "spo2":
            vitals["spo2"] = f"{int(r.primary_value)}%"
        elif r.metric_type == "heart_rate":
            vitals["heart_rate"] = f"{int(r.primary_value)} bpm"
        elif r.metric_type == "temperature":
            vitals["temperature"] = f"{r.primary_value} {r.unit}"
    return vitals


def fetch_latest_medications(db: Session, patient: User) -> Optional[str]:
    if patient.current_medications and patient.current_medications.strip():
        return patient.current_medications
    latest_rx = (
        db.query(Prescription)
        .join(Consultation, Prescription.consultation_id == Consultation.id)
        .filter(Consultation.patient_id == patient.id)
        .order_by(Prescription.created_at.desc())
        .first()
    )
    if not latest_rx:
        return None
    try:
        items = json.loads(latest_rx.medicines_json or "[]")
        names = []
        for item in items:
            if isinstance(item, dict):
                names.append(item.get("name") or item.get("medicine") or str(item))
            else:
                names.append(str(item))
        return ", ".join(names) if names else None
    except Exception:
        return latest_rx.medicines_json


def fetch_relevant_physician(db: Session, patient: User) -> Dict[str, Any]:
    consult = (
        db.query(Consultation)
        .filter(Consultation.patient_id == patient.id, Consultation.doctor_id.isnot(None))
        .order_by(Consultation.created_at.desc())
        .first()
    )
    if not consult or not consult.doctor_id:
        return {}
    doctor = db.query(User).filter(User.id == consult.doctor_id).first()
    profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == consult.doctor_id).first()
    return {
        "name": doctor.full_name if doctor else None,
        "specialization": profile.specialization if profile else None,
        "hospital": profile.hospital_affiliation if profile else None,
        "license_number": profile.license_number if profile else None,
    }


def build_live_passport(db: Session, patient: User) -> Dict[str, Any]:
    return assemble_live_emergency_passport(
        patient,
        latest_vitals=fetch_latest_vitals(db, patient.id),
        latest_medications=fetch_latest_medications(db, patient),
        physician=fetch_relevant_physician(db, patient),
    )


def passport_to_context_fields(passport: Dict[str, Any]) -> Dict[str, Any]:
    """Map live passport fields onto the existing contextual QR filter keys."""
    vitals = passport.get("latest_vitals_snapshot") or {}
    physician = passport.get("physician") or {}
    physician_line = ", ".join(
        str(physician.get(k))
        for k in ("name", "specialization", "hospital")
        if physician.get(k) and physician.get(k) != "Not recorded"
    )
    return {
        "full_name": passport.get("full_name"),
        "age": passport.get("age"),
        "gender": passport.get("gender"),
        "blood_group": passport.get("blood_group"),
        "drug_allergies": passport.get("drug_allergies"),
        "emergency_contact_phone": passport.get("emergency_contact_phone"),
        "pre_existing_conditions": passport.get("pre_existing_conditions"),
        "current_medications": passport.get("current_medications"),
        "recent_vitals": vitals,
        "treating_physician_notes": physician_line or passport.get("treating_physician_notes"),
        "patient_id": passport.get("patient_id"),
        "generated_dynamically": True,
        "read_only": True,
    }


def record_emergency_access(
    db: Session,
    *,
    accessor: Optional[User],
    patient_id: int,
    purpose: Optional[str],
    information_type: str,
    is_emergency: bool,
    access_channel: str,
    context_scope: Optional[str] = None,
    accessor_name: Optional[str] = None,
    accessor_role: Optional[str] = None,
) -> EmergencyAccessAudit:
    rec = EmergencyAccessAudit(
        accessor_id=accessor.id if accessor else None,
        accessor_role=accessor_role or (accessor.role if accessor else "anonymous"),
        accessor_name=accessor_name or (accessor.full_name if accessor else "QR / public responder"),
        patient_id=patient_id,
        accessed_at=datetime.utcnow(),
        purpose=(purpose or "")[:255] or None,
        information_type=information_type[:120],
        is_emergency=is_emergency,
        access_channel=access_channel[:50],
        context_scope=context_scope,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def serialize_audit_row(row: EmergencyAccessAudit) -> Dict[str, Any]:
    """Admin/audit UI payload without clinical content."""
    return {
        "id": row.id,
        "accessor_id": row.accessor_id,
        "accessor_name": row.accessor_name,
        "accessor_role": row.accessor_role,
        "patient_id": row.patient_id,
        "timestamp": row.accessed_at.isoformat() if row.accessed_at else None,
        "purpose": row.purpose,
        "information_type": row.information_type,
        "is_emergency": bool(row.is_emergency),
        "access_channel": row.access_channel,
        "context_scope": row.context_scope,
    }
