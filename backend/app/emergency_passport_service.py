"""Shared live emergency passport assembly and access auditing."""
import json
from datetime import datetime, timedelta, timezone
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


def grade_vital_reading(metric_type: str, primary_val: float, secondary_val: Optional[float] = None) -> Dict[str, Any]:
    status = "NORMAL"
    flag = "Optimal physiological reading"
    if metric_type == "blood_pressure":
        sys = primary_val
        dia = secondary_val or 80.0
        if sys >= 160 or dia >= 100:
            status = "CRITICAL"
            flag = f"Stage 2 Hypertensive Urgency ({int(sys)}/{int(dia)} mmHg)"
        elif sys >= 140 or dia >= 90:
            status = "BORDERLINE"
            flag = f"Stage 1 Elevated Pressure ({int(sys)}/{int(dia)} mmHg)"
        elif sys < 90 or dia < 60:
            status = "BORDERLINE"
            flag = f"Hypotension Warning ({int(sys)}/{int(dia)} mmHg)"
        else:
            status = "NORMAL"
            flag = f"Optimal Blood Pressure ({int(sys)}/{int(dia)} mmHg)"
    elif metric_type == "spo2":
        if primary_val < 90:
            status = "CRITICAL"
            flag = f"Critical Hypoxemia Alert ({int(primary_val)}%)"
        elif primary_val < 95:
            status = "BORDERLINE"
            flag = f"Sub-optimal Oxygen Saturation ({int(primary_val)}%)"
        else:
            status = "NORMAL"
            flag = f"Normal Oxygen Saturation ({int(primary_val)}%)"
    elif metric_type == "heart_rate":
        if primary_val > 115:
            status = "CRITICAL"
            flag = f"Sinus Tachycardia Alert ({int(primary_val)} bpm)"
        elif primary_val < 50:
            status = "BORDERLINE"
            flag = f"Sinus Bradycardia ({int(primary_val)} bpm)"
        else:
            status = "NORMAL"
            flag = f"Normal Resting Heart Rate ({int(primary_val)} bpm)"
    elif metric_type == "glucose":
        if primary_val >= 200 or primary_val < 60:
            status = "CRITICAL"
            flag = f"Critical Glucose Imbalance ({int(primary_val)} mg/dL)"
        elif primary_val >= 140:
            status = "BORDERLINE"
            flag = f"Elevated Fasting Glucose ({int(primary_val)} mg/dL)"
        else:
            status = "NORMAL"
            flag = f"Normal Euglycemia ({int(primary_val)} mg/dL)"
    return {"status": status, "flag": flag}


def fetch_latest_vitals(db: Session, patient_id: int) -> Dict[str, Any]:
    latest_rows = (
        db.query(IoTVitalReading)
        .filter(IoTVitalReading.patient_id == patient_id)
        .order_by(IoTVitalReading.recorded_at.desc())
        .limit(16)
        .all()
    )
    vitals: Dict[str, Any] = {}
    graded: Dict[str, Any] = {}

    for r in latest_rows:
        if r.metric_type in vitals:
            continue
        grade_info = grade_vital_reading(r.metric_type, r.primary_value, r.secondary_value)
        time_str = r.recorded_at.strftime("%I:%M %p, %b %d") if r.recorded_at else "Recent"
        src_label = "IoT Continuous Monitor" if r.source == "iot_wearable" else "Clinical Measurement"

        if r.metric_type == "blood_pressure":
            val = f"{int(r.primary_value)}/{int(r.secondary_value or 80)} mmHg"
            vitals["blood_pressure"] = val
            graded["blood_pressure"] = {
                "metric": "Blood Pressure",
                "value": val,
                "status": grade_info["status"],
                "flag": grade_info["flag"],
                "recorded_at": time_str,
                "source": src_label
            }
        elif r.metric_type == "glucose":
            val = f"{int(r.primary_value)} mg/dL"
            vitals["glucose"] = val
            graded["glucose"] = {
                "metric": "Blood Glucose",
                "value": val,
                "status": grade_info["status"],
                "flag": grade_info["flag"],
                "recorded_at": time_str,
                "source": src_label
            }
        elif r.metric_type == "spo2":
            val = f"{int(r.primary_value)}%"
            vitals["spo2"] = val
            graded["spo2"] = {
                "metric": "Oxygen Saturation (SpO2)",
                "value": val,
                "status": grade_info["status"],
                "flag": grade_info["flag"],
                "recorded_at": time_str,
                "source": src_label
            }
        elif r.metric_type == "heart_rate":
            val = f"{int(r.primary_value)} bpm"
            vitals["heart_rate"] = val
            graded["heart_rate"] = {
                "metric": "Heart Rate",
                "value": val,
                "status": grade_info["status"],
                "flag": grade_info["flag"],
                "recorded_at": time_str,
                "source": src_label
            }
        elif r.metric_type == "temperature":
            val = f"{r.primary_value} {r.unit}"
            vitals["temperature"] = val
            graded["temperature"] = {
                "metric": "Body Temperature",
                "value": val,
                "status": "NORMAL",
                "flag": "Normal Core Temperature",
                "recorded_at": time_str,
                "source": src_label
            }

    # If patient has no IoT readings recorded yet, provide clinical baseline structure
    if not vitals:
        vitals = {
            "blood_pressure": "120/80 mmHg",
            "heart_rate": "72 bpm",
            "spo2": "98%",
            "glucose": "95 mg/dL",
        }
        graded = {
            "blood_pressure": {
                "metric": "Blood Pressure",
                "value": "120/80 mmHg",
                "status": "NORMAL",
                "flag": "Optimal Baseline (Demo Baseline)",
                "recorded_at": "Today (Demo Sensor)",
                "source": "Simulated Demo Device"
            },
            "heart_rate": {
                "metric": "Heart Rate",
                "value": "72 bpm",
                "status": "NORMAL",
                "flag": "Normal Resting Rate (Demo Baseline)",
                "recorded_at": "Today (Demo Sensor)",
                "source": "Simulated Demo Device"
            },
            "spo2": {
                "metric": "Oxygen Saturation (SpO2)",
                "value": "98%",
                "status": "NORMAL",
                "flag": "Normal Oxygenation (Demo Baseline)",
                "recorded_at": "Today (Demo Sensor)",
                "source": "Simulated Demo Device"
            },
            "glucose": {
                "metric": "Blood Glucose",
                "value": "95 mg/dL",
                "status": "NORMAL",
                "flag": "Normal Fasting (Demo Baseline)",
                "recorded_at": "Today (Demo Sensor)",
                "source": "Simulated Demo Device"
            }
        }

    vitals["graded_vitals"] = graded
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
    """Map live passport fields onto the contextual QR filter keys."""
    vitals = passport.get("latest_vitals_snapshot") or {}
    graded_vitals = passport.get("recent_vitals", {}).get("graded_vitals") or vitals.get("graded_vitals") or {}
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
        "severe_drug_allergies": passport.get("severe_drug_allergies"),
        "allergy_status": passport.get("allergy_status"),
        "emergency_contact": passport.get("emergency_contact"),
        "emergency_contact_name": passport.get("emergency_contact_name"),
        "emergency_contact_phone": passport.get("emergency_contact_phone"),
        "resuscitation_preference": passport.get("resuscitation_preference", "Full Resuscitation (Unless DNR explicitly ordered)"),
        "pre_existing_conditions": passport.get("pre_existing_conditions"),
        "condition_status": passport.get("condition_status"),
        "current_medications": passport.get("current_medications"),
        "medication_status": passport.get("medication_status"),
        "recent_vitals": vitals,
        "graded_vitals": graded_vitals,
        "treating_physician_notes": physician_line or passport.get("treating_physician_notes"),
        "physician": physician,
        "profile_completion": passport.get("profile_completion"),
        "is_verified": passport.get("is_verified", False),
        "verified_at": passport.get("verified_at"),
        "verified_by": passport.get("verified_by"),
        "last_updated_at": passport.get("last_updated_at"),
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
    status: str = "SUCCESS",
    consent_status: str = "GRANTED",
    expires_at: Optional[datetime] = None,
    revoked_at: Optional[datetime] = None,
    fields_viewed: Optional[Any] = None,
    anomaly_detected: bool = False,
    anomaly_reason: Optional[str] = None,
) -> EmergencyAccessAudit:
    # Serialize fields_viewed as JSON string if passed as list/dict
    fields_str = None
    if fields_viewed is not None:
        fields_str = json.dumps(fields_viewed) if not isinstance(fields_viewed, str) else fields_viewed

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
        status=status[:30],
        consent_status=consent_status[:30],
        expires_at=expires_at,
        revoked_at=revoked_at,
        fields_viewed=fields_str,
        anomaly_detected=anomaly_detected,
        anomaly_reason=anomaly_reason[:255] if anomaly_reason else None,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


def serialize_audit_row(row: EmergencyAccessAudit) -> Dict[str, Any]:
    """Admin/audit UI payload with rich access security metadata and viewed fields."""
    parsed_fields = []
    if row.fields_viewed:
        try:
            parsed_fields = json.loads(row.fields_viewed)
        except Exception:
            parsed_fields = [row.fields_viewed]

    status_badge = "bg-success"
    if row.status == "DENIED":
        status_badge = "bg-danger"
    elif row.status == "EXPIRED":
        status_badge = "bg-warning text-dark"
    elif row.status == "REVOKED":
        status_badge = "bg-secondary text-white"
    elif row.status == "RATE_LIMITED":
        status_badge = "bg-danger text-white"

    ist_tz = timezone(timedelta(hours=5, minutes=30))
    timestamp_ist = None
    if row.accessed_at:
        try:
            dt_utc = row.accessed_at if row.accessed_at.tzinfo else row.accessed_at.replace(tzinfo=timezone.utc)
            timestamp_ist = dt_utc.astimezone(ist_tz).strftime("%d %b %Y, %I:%M:%S %p IST")
        except Exception:
            timestamp_ist = row.accessed_at.strftime("%d %b %Y, %I:%M:%S %p IST")

    return {
        "id": row.id,
        "accessor_id": row.accessor_id,
        "accessor_name": row.accessor_name,
        "accessor_role": row.accessor_role,
        "patient_id": row.patient_id,
        "timestamp": row.accessed_at.isoformat() if row.accessed_at else None,
        "timestamp_ist": timestamp_ist,
        "purpose": row.purpose,
        "information_type": row.information_type,
        "is_emergency": bool(row.is_emergency),
        "access_channel": row.access_channel,
        "context_scope": row.context_scope,
        "status": row.status or "SUCCESS",
        "status_badge": status_badge,
        "consent_status": row.consent_status or "GRANTED",
        "expires_at": row.expires_at.isoformat() if row.expires_at else None,
        "revoked_at": row.revoked_at.isoformat() if row.revoked_at else None,
        "fields_viewed": parsed_fields,
        "anomaly_detected": bool(row.anomaly_detected),
        "anomaly_reason": row.anomaly_reason,
    }
