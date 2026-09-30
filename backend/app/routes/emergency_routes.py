import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, EmergencyAlert, IoTVitalReading
from ..auth import get_current_user
from ..ml.emergency_engine import (
    build_emergency_medical_passport,
    calculate_ambulance_telemetry,
    EMERGENCY_HOSPITALS
)

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

    patient_dict = {
        "full_name": current_user.full_name,
        "age": current_user.age or 48,
        "gender": current_user.gender or "Male",
        "blood_group": current_user.blood_group or "B+",
        "drug_allergies": current_user.drug_allergies or "Penicillin, Amoxicillin",
        "pre_existing_conditions": current_user.pre_existing_conditions or "Diabetes Type 2, Hypertension",
        "current_medications": current_user.current_medications or "Metformin 500mg, Telmisartan 40mg",
        "phone": current_user.phone or "+91 91234 56789"
    }

    passport = build_emergency_medical_passport(patient_dict, vitals_dict)
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
        blood_bank_alert=f"{patient_dict['blood_group']} Pre-Match Dispatched",
        patient_snapshot=json.dumps(passport),
        status="dispatched"
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    AMBULANCE_STEP_TRACKER[alert.id] = 1

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
    current_user: User = Depends(get_current_user),
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
            "patient_name": p.full_name if p else "Emergency Patient",
            "age": p.age if p else None,
            "blood_group": p.blood_group if p else "O+",
            "emergency_type": a.emergency_type,
            "ambulance_unit": a.ambulance_unit,
            "eta_minutes": a.eta_minutes,
            "trauma_bay": a.reserved_trauma_bay,
            "status": a.status,
            "allergies": passport.get("severe_drug_allergies", "None"),
            "vitals": passport.get("latest_vitals_snapshot", {}),
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
