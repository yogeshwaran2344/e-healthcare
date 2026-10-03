import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, EmergencyAlert, IoTVitalReading
from ..auth import get_current_user, require_roles
from ..ml.emergency_engine import (
    build_emergency_medical_passport,
    calculate_ambulance_telemetry,
    EMERGENCY_HOSPITALS
)
from ..emergency_passport_service import (
    build_live_passport,
    record_emergency_access,
    serialize_audit_row,
)
from ..models import EmergencyAccessAudit

router = APIRouter(prefix="/api/emergency", tags=["Emergency Response & Ambulance"])

# Memory counter to simulate smooth real-time ambulance tracking steps
AMBULANCE_STEP_TRACKER = {}

@router.post("/trigger-sos")
def trigger_rapid_sos(
    payload: Dict[str, Any] = Body(default={}),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    One-Tap SOS Dispatcher:
    - Generates Emergency Medical Passport (Allergies, Blood Group, Conditions, Meds, Vitals)
    - Dispatches nearest Advanced Life Support (ALS) Ambulance
    - Pre-allocates ER trauma bay bed and alerts blood bank.
    """
    lat = float(payload.get("latitude", 12.9716))
    lng = float(payload.get("longitude", 77.5946))
    emergency_type = payload.get("emergency_type", "SOS_MANUAL")

    # Fetch latest vitals
    latest_r = (
        db.query(IoTVitalReading)
        .filter(IoTVitalReading.patient_id == current_user.id)
        .order_by(IoTVitalReading.recorded_at.desc())
        .limit(4)
        .all()
    )
    vitals_dict = {}
    for r in latest_r:
        if r.metric_type == "blood_pressure":
            vitals_dict["blood_pressure"] = f"{int(r.primary_value)}/{int(r.secondary_value or 80)} mmHg"
        elif r.metric_type == "glucose":
            vitals_dict["glucose"] = f"{int(r.primary_value)} mg/dL"
        elif r.metric_type == "spo2":
            vitals_dict["spo2"] = f"{int(r.primary_value)}%"
        elif r.metric_type == "heart_rate":
            vitals_dict["heart_rate"] = f"{int(r.primary_value)} bpm"

    passport = build_live_passport(db, current_user)
    telemetry = calculate_ambulance_telemetry(lat, lng, current_step=1, total_steps=6)

    alert = EmergencyAlert(
        patient_id=current_user.id,
        emergency_type=emergency_type,
        severity="CRITICAL",
        patient_latitude=lat,
        patient_longitude=lng,
        ambulance_unit=telemetry["ambulance_unit"],
        paramedic_name=telemetry["paramedic_team"],
        paramedic_contact=telemetry["ambulance_phone"],
        ambulance_lat=telemetry["latitude"],
        ambulance_lng=telemetry["longitude"],
        eta_minutes=telemetry["eta_minutes"],
        hospital_destination=telemetry["receiving_hospital"],
        reserved_trauma_bay=telemetry["assigned_trauma_bay"],
        blood_bank_alert=f"{passport.get('blood_group', 'Unknown')} Pre-Match Dispatched",
        patient_snapshot=json.dumps(passport),
        status="dispatched"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    AMBULANCE_STEP_TRACKER[alert.id] = 1

    record_emergency_access(
        db,
        accessor=current_user,
        patient_id=current_user.id,
        purpose="One-tap SOS dispatch",
        information_type="emergency_passport",
        is_emergency=True,
        access_channel="sos",
        context_scope="SOS_DISPATCH",
    )

    return {
        "status": "EMERGENCY_DISPATCHED",
        "alert_id": alert.id,
        "eta_minutes": alert.eta_minutes,
        "ambulance_unit": alert.ambulance_unit,
        "paramedic_team": alert.paramedic_name,
        "paramedic_phone": alert.paramedic_contact,
        "destination_hospital": alert.hospital_destination,
        "assigned_trauma_bay": alert.reserved_trauma_bay,
        "patient_passport_shared": passport
    }

@router.get("/active-status")
def get_active_emergency_status(
    alert_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns live dynamic GPS telemetry of dispatched ambulance, distance, and ETA.
    """
    query = db.query(EmergencyAlert)
    if alert_id:
        query = query.filter(EmergencyAlert.id == alert_id)
    else:
        query = query.filter(EmergencyAlert.patient_id == current_user.id, EmergencyAlert.status != "resolved")

    alert = query.order_by(EmergencyAlert.created_at.desc()).first()
    if not alert:
        return {"has_active_emergency": False, "alert": None}

    # Progress step simulation
    step = AMBULANCE_STEP_TRACKER.get(alert.id, 1)
    step = min(6, step + 1)
    AMBULANCE_STEP_TRACKER[alert.id] = step

    telemetry = calculate_ambulance_telemetry(
        alert.patient_latitude,
        alert.patient_longitude,
        current_step=step,
        total_steps=6
    )

    alert.ambulance_lat = telemetry["latitude"]
    alert.ambulance_lng = telemetry["longitude"]
    alert.eta_minutes = telemetry["eta_minutes"]
    alert.status = telemetry["status"]
    db.commit()

    passport_data = json.loads(alert.patient_snapshot) if alert.patient_snapshot else {}

    return {
        "has_active_emergency": True,
        "alert_id": alert.id,
        "emergency_type": alert.emergency_type,
        "telemetry": telemetry,
        "hospital_destination": alert.hospital_destination,
        "reserved_trauma_bay": alert.reserved_trauma_bay,
        "blood_bank_status": alert.blood_bank_alert,
        "shared_medical_passport": passport_data
    }

@router.get("/doctor-feed")
def get_hospital_er_feed(
    current_user: User = Depends(require_roles("doctor", "admin")),
    db: Session = Depends(get_db)
):
    """
    Hospital Inbound ER Emergency Dashboard showing arriving ambulances and critical patients.
    """
    alerts = (
        db.query(EmergencyAlert)
        .order_by(EmergencyAlert.created_at.desc())
        .limit(8)
        .all()
    )

    feed = []
    for a in alerts:
        p = db.query(User).filter(User.id == a.patient_id).first()
        passport = json.loads(a.patient_snapshot) if a.patient_snapshot else {}
        feed.append({
            "id": a.id,
            "patient_id": a.patient_id,
            "patient_name": p.full_name if p else "Emergency Patient",
            "age": p.age if p else None,
            "blood_group": (p.blood_group if p and p.blood_group else None)
            or passport.get("blood_group")
            or "Not recorded",
            "emergency_type": a.emergency_type,
            "ambulance_unit": a.ambulance_unit,
            "eta_minutes": a.eta_minutes,
            "trauma_bay": a.reserved_trauma_bay,
            "status": a.status,
            "allergies": passport.get("severe_drug_allergies")
            or passport.get("drug_allergies")
            or "Not recorded",
            "vitals": passport.get("latest_vitals_snapshot") or {},
            "created_at": a.created_at
        })

    return {
        "total_active_er_cases": len([x for x in feed if x["status"] != "resolved"]),
        "inbound_emergencies": feed
    }

@router.post("/resolve/{alert_id}")
def resolve_emergency(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Marks emergency as resolved."""
    alert = db.query(EmergencyAlert).filter(EmergencyAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    db.commit()
    return {"message": "Emergency alert marked as resolved and closed."}


def _authorize_passport_access(current_user: User, patient: User) -> None:
    if current_user.id == patient.id and current_user.role == "patient":
        return
    if current_user.role in ("doctor", "admin"):
        return
    raise HTTPException(status_code=403, detail="Not authorized to view this emergency passport.")


@router.get("/live-passport")
def get_own_live_emergency_passport(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Patient (or clinician viewing self) live emergency passport from current authorized records.
    """
    if current_user.role not in ("patient", "doctor", "admin"):
        raise HTTPException(status_code=403, detail="Not authorized.")

    target = current_user
    if current_user.role != "patient":
        raise HTTPException(
            status_code=400,
            detail="Clinicians must request a specific patient via /api/emergency/live-passport/{patient_id}.",
        )

    passport = build_live_passport(db, target)
    record_emergency_access(
        db,
        accessor=current_user,
        patient_id=target.id,
        purpose="Patient self-view of live emergency passport",
        information_type="emergency_passport",
        is_emergency=False,
        access_channel="authenticated",
        context_scope="SELF",
    )
    return {"passport": passport, "mode": "emergency-self"}


@router.get("/live-passport/{patient_id}")
def get_patient_live_emergency_passport(
    patient_id: int,
    purpose: str = Query(..., min_length=8, description="Clinical purpose / reason for access"),
    is_emergency: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Role-gated live emergency passport. Doctors/admins provide a purpose; patients may only read self.
    """
    patient = db.query(User).filter(User.id == patient_id, User.role == "patient").first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found.")

    _authorize_passport_access(current_user, patient)

    if current_user.role == "patient" and current_user.id != patient.id:
        raise HTTPException(status_code=403, detail="Patients may only view their own emergency passport.")

    passport = build_live_passport(db, patient)
    record_emergency_access(
        db,
        accessor=current_user,
        patient_id=patient.id,
        purpose=purpose,
        information_type="emergency_passport",
        is_emergency=is_emergency,
        access_channel="authenticated",
        context_scope="HOSPITAL_ER_TRAUMA" if current_user.role in ("doctor", "admin") else "SELF",
    )
    return {
        "passport": passport,
        "mode": "emergency" if is_emergency else "non-emergency",
        "read_only": True,
    }


@router.get("/audit-log")
def get_emergency_access_audit_log(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Audit history without clinical payload. Admin: all events. Doctor: own accesses.
    Patient: accesses involving their own record.
    """
    query = db.query(EmergencyAccessAudit).order_by(EmergencyAccessAudit.accessed_at.desc())

    if current_user.role == "admin":
        if patient_id:
            query = query.filter(EmergencyAccessAudit.patient_id == patient_id)
    elif current_user.role == "doctor":
        query = query.filter(EmergencyAccessAudit.accessor_id == current_user.id)
        if patient_id:
            query = query.filter(EmergencyAccessAudit.patient_id == patient_id)
    elif current_user.role == "patient":
        query = query.filter(EmergencyAccessAudit.patient_id == current_user.id)
    else:
        raise HTTPException(status_code=403, detail="Not authorized to view emergency access audits.")

    rows = query.limit(200).all()
    return {
        "total": len(rows),
        "events": [serialize_audit_row(r) for r in rows],
        "note": "Audit entries list accessor, patient id, time, purpose, and access type only. Clinical details are omitted.",
    }
