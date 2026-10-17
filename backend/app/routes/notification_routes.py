"""
Fast2SMS Notifications & Automated Clinical Alerts API Routes
Exposes endpoints for:
1. Patient medication reminders (immediate and scheduled)
2. Caretaker vital signs alerts with clinical threshold monitoring
3. Caretaker configuration management
4. Direct Fast2SMS cellular SMS testing & diagnostics
"""

import os
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, MedicationSchedule, CaretakerAlertConfig, IoTVitalReading
from ..auth import get_current_user
from ..sms_service import (
    send_sms,
    get_fast2sms_config,
    check_sms_service_health,
    sanitize_indian_mobile_number
)
from ..medication_reminders import send_medication_reminder, check_and_send_due_reminders
from ..health_alerts import check_vitals, DEFAULT_BP_LIMITS, DEFAULT_HR_LIMITS

router = APIRouter(prefix="/api/notifications", tags=["Notifications & Reminders"])


@router.get("/sms/status")
def get_sms_status(current_user: User = Depends(get_current_user)):
    """
    Checks Fast2SMS configuration status for authenticated users.
    Returns whether Fast2SMS credentials are configured in .env.
    """
    cfg = get_fast2sms_config()
    is_configured = bool(cfg.get("api_key"))

    return {
        "provider": "Fast2SMS",
        "configured": is_configured,
        "route": cfg.get("route", "q"),
        "default_recipient": cfg.get("default_recipient"),
        "requires_dlt": False,
        "automated": True
    }


@router.get("/status")
def get_notification_system_status():
    """
    Returns the real-time operational status of the Fast2SMS Quick Gateway service.
    """
    health = check_sms_service_health()
    return {
        "service": "NeuroCare Automated SMS Gateway",
        "health": health,
        "workflows": {
            "workflow_1": "Patient Medication Reminders (Automated Dose Schedules)",
            "workflow_2": "Caretaker Vital Signs Health Alerts (BP & Heart Rate Monitoring)"
        },
        "checked_at": datetime.utcnow().isoformat()
    }


@router.post("/whatsapp/test")
@router.post("/sms/test")
@router.post("/sms/send")
def test_sms_message(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Direct diagnostic endpoint to test cellular SMS dispatch to a specified phone number.
    """
    phone = (payload.get("phone") or current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")).strip()
    message = payload.get("message", "Test notification from NeuroCare Platform: Cellular SMS gateway verified.").strip()
    
    result = send_sms(phone, message)
    return {
        "requested_phone": phone,
        "result": result
    }


# =====================================================================
# WORKFLOW 1: PATIENT MEDICATION REMINDERS
# =====================================================================

@router.post("/reminders/send-immediate")
def trigger_immediate_medication_reminder(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Workflow 1: Sends an immediate medication reminder cellular SMS to the patient.
    """
    med_name = payload.get("medication_name", "Prescribed Medication")
    dosage = payload.get("dosage", "")
    time_str = payload.get("scheduled_time", datetime.now().strftime("%I:%M %p"))
    patient_phone = (payload.get("patient_phone") or current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")).strip()
    patient_name = payload.get("patient_name", current_user.full_name or "Patient")

    res = send_medication_reminder(
        patient_phone=patient_phone,
        medication_name=med_name,
        scheduled_time=time_str,
        dosage=dosage,
        patient_name=patient_name
    )

    return {
        "status": "success" if res.get("success") else "failed",
        "reminder_details": {
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "medication_name": med_name,
            "dosage": dosage,
            "scheduled_time": time_str
        },
        "dispatch_result": res
    }


@router.post("/reminders/schedules/create")
def create_medication_schedule(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Creates a new recurring medication reminder schedule for the logged-in patient."""
    med_name = payload.get("medication_name", "").strip()
    sched_time = payload.get("scheduled_time", "").strip()

    if not med_name or not sched_time:
        raise HTTPException(status_code=400, detail="medication_name and scheduled_time are required.")

    phone = (payload.get("patient_phone") or current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")).strip()

    sched = MedicationSchedule(
        patient_id=current_user.id,
        medication_name=med_name,
        dosage=payload.get("dosage", ""),
        scheduled_time=sched_time,
        patient_phone=phone,
        notes=payload.get("notes", ""),
        is_active=True
    )
    db.add(sched)
    db.commit()
    db.refresh(sched)

    return {
        "success": True,
        "message": f"Medication schedule for {med_name} created.",
        "schedule": {
            "id": sched.id,
            "medication_name": sched.medication_name,
            "dosage": sched.dosage,
            "scheduled_time": sched.scheduled_time,
            "patient_phone": sched.patient_phone,
            "is_active": sched.is_active
        }
    }


@router.get("/reminders/schedules")
def list_medication_schedules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists all active medication schedules for the current patient."""
    schedules = db.query(MedicationSchedule).filter(
        MedicationSchedule.patient_id == current_user.id
    ).all()

    return [
        {
            "id": s.id,
            "medication_name": s.medication_name,
            "dosage": s.dosage,
            "scheduled_time": s.scheduled_time,
            "patient_phone": s.patient_phone,
            "notes": s.notes,
            "is_active": s.is_active,
            "last_reminded_date": s.last_reminded_date,
            "last_status": s.last_status,
            "created_at": s.created_at
        }
        for s in schedules
    ]


@router.post("/reminders/check-due")
def trigger_due_reminders_check(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually triggers due dose check across database schedules.
    Dispatches automated SMS for any dose scheduled for the current minute.
    """
    dispatched = check_and_send_due_reminders(db=db)
    return {
        "status": "completed",
        "dispatched_count": len(dispatched),
        "dispatched_reminders": dispatched
    }


# =====================================================================
# WORKFLOW 2: CARETAKER HEALTH ALERTS
# =====================================================================

@router.post("/vitals/evaluate-alert")
def evaluate_vitals_and_alert(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Workflow 2: Evaluates patient BP and Heart Rate against configured clinical thresholds.
    If outside configured safe range, immediately transmits a cellular SMS health alert to the registered caretaker.
    """
    systolic_bp = float(payload.get("systolic_bp", 120.0))
    diastolic_bp = float(payload.get("diastolic_bp", 80.0))
    heart_rate = float(payload.get("heart_rate", 75.0))
    bypass_cooldown = bool(payload.get("bypass_cooldown", False))

    patient_name = payload.get("patient_name", current_user.full_name or "Patient")
    patient_id = payload.get("patient_id", current_user.id)

    # Resolve caretaker contact & custom thresholds from DB
    caretaker_phone = payload.get("caretaker_phone")
    bp_limits = DEFAULT_BP_LIMITS
    hr_limits = DEFAULT_HR_LIMITS

    cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == patient_id).first()
    if cfg and cfg.is_active:
        if not caretaker_phone:
            caretaker_phone = cfg.caretaker_phone
        bp_limits = (cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max)
        hr_limits = (cfg.heart_rate_min, cfg.heart_rate_max)

    if not caretaker_phone:
        caretaker_phone = current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")

    # Allow custom limit overrides from payload if provided
    if "bp_limits" in payload and len(payload["bp_limits"]) == 4:
        bp_limits = tuple(map(float, payload["bp_limits"]))
    if "heart_rate_limits" in payload and len(payload["heart_rate_limits"]) == 2:
        hr_limits = tuple(map(float, payload["heart_rate_limits"]))

    result = check_vitals(
        patient_id=str(patient_id),
        caretaker_phone=caretaker_phone,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        heart_rate=heart_rate,
        bp_limits=bp_limits,
        heart_rate_limits=hr_limits,
        patient_name=patient_name,
        bypass_cooldown=bypass_cooldown
    )

    return result


@router.get("/caretaker/config")
def get_caretaker_config(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieves patient's current caretaker alert routing and threshold configurations."""
    cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == current_user.id).first()
    if not cfg:
        return {
            "configured": False,
            "defaults": {
                "bp_limits": list(DEFAULT_BP_LIMITS),
                "heart_rate_limits": list(DEFAULT_HR_LIMITS),
                "caretaker_phone": current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755")
            }
        }

    return {
        "configured": True,
        "config": {
            "caretaker_name": cfg.caretaker_name,
            "caretaker_phone": cfg.caretaker_phone,
            "relationship": cfg.relationship,
            "bp_limits": [cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max],
            "heart_rate_limits": [cfg.heart_rate_min, cfg.heart_rate_max],
            "is_active": cfg.is_active,
            "updated_at": cfg.updated_at
        }
    }


@router.post("/caretaker/config")
def save_caretaker_config(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Saves or updates clinician-configured vital thresholds and caretaker phone number.
    """
    cfg = db.query(CaretakerAlertConfig).filter(CaretakerAlertConfig.patient_id == current_user.id).first()
    if not cfg:
        cfg = CaretakerAlertConfig(patient_id=current_user.id)
        db.add(cfg)

    cfg.caretaker_name = payload.get("caretaker_name", cfg.caretaker_name or "Primary Caregiver")
    cfg.caretaker_phone = payload.get("caretaker_phone", cfg.caretaker_phone or current_user.phone or os.getenv("DEFAULT_ALERT_RECIPIENT", "+918618912755"))
    cfg.relationship = payload.get("relationship", cfg.relationship or "Guardian")

    if "bp_limits" in payload and len(payload["bp_limits"]) == 4:
        cfg.systolic_min = float(payload["bp_limits"][0])
        cfg.systolic_max = float(payload["bp_limits"][1])
        cfg.diastolic_min = float(payload["bp_limits"][2])
        cfg.diastolic_max = float(payload["bp_limits"][3])

    if "heart_rate_limits" in payload and len(payload["heart_rate_limits"]) == 2:
        cfg.heart_rate_min = float(payload["heart_rate_limits"][0])
        cfg.heart_rate_max = float(payload["heart_rate_limits"][1])

    cfg.is_active = bool(payload.get("is_active", True))
    cfg.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(cfg)

    return {
        "success": True,
        "message": "Caretaker alert thresholds and phone number saved successfully.",
        "config": {
            "caretaker_name": cfg.caretaker_name,
            "caretaker_phone": cfg.caretaker_phone,
            "bp_limits": [cfg.systolic_min, cfg.systolic_max, cfg.diastolic_min, cfg.diastolic_max],
            "heart_rate_limits": [cfg.heart_rate_min, cfg.heart_rate_max],
            "is_active": cfg.is_active
        }
    }
