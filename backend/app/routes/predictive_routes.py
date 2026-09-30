from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from ..database import get_db
from ..models import User, Consultation, IoTVitalReading, PredictiveFollowUp, ChronicAlert
from ..auth import get_current_user
from ..ml.predictive_care_engine import calculate_predictive_deterioration_risk, generate_chronic_ai_alerts

router = APIRouter(prefix="/api/predictive", tags=["AI Predictive Care"])

@router.get("/assessment")
def get_predictive_assessment(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes real-time predictive risk score and recommends follow-up timeline
    before issues escalate into acute emergencies.
    """
    # Fetch recent consultations
    recent_consultations = (
        db.query(Consultation)
        .filter(Consultation.patient_id == current_user.id)
        .order_by(Consultation.created_at.desc())
        .limit(3)
        .all()
    )
    consultation_dicts = [
        {"triage_level": c.triage_level, "disease": c.predicted_disease}
        for c in recent_consultations
    ]

    # Fetch latest IoT vitals if available
    latest_readings = (
        db.query(IoTVitalReading)
        .filter(IoTVitalReading.patient_id == current_user.id)
        .order_by(IoTVitalReading.recorded_at.desc())
        .limit(10)
        .all()
    )
    vitals_dict = {}
    for r in latest_readings:
        if r.metric_type == "blood_pressure" and "systolic_bp" not in vitals_dict:
            vitals_dict["systolic_bp"] = r.primary_value
            vitals_dict["diastolic_bp"] = r.secondary_value
        elif r.metric_type == "glucose" and "glucose" not in vitals_dict:
            vitals_dict["glucose"] = r.primary_value
        elif r.metric_type == "spo2" and "spo2" not in vitals_dict:
            vitals_dict["spo2"] = r.primary_value

    patient_context = {
        "full_name": current_user.full_name,
        "age": current_user.age or 45,
        "pre_existing_conditions": current_user.pre_existing_conditions or "",
        "drug_allergies": current_user.drug_allergies or ""
    }

    assessment = calculate_predictive_deterioration_risk(
        patient_context=patient_context,
        recent_consultations=consultation_dicts,
        latest_vitals=vitals_dict
    )

    # Check if a follow-up record exists or create one
    existing_followup = (
        db.query(PredictiveFollowUp)
        .filter(PredictiveFollowUp.patient_id == current_user.id)
        .order_by(PredictiveFollowUp.created_at.desc())
        .first()
    )
    if not existing_followup:
        existing_followup = PredictiveFollowUp(
            patient_id=current_user.id,
            risk_score=assessment["risk_score"],
            urgency_level=assessment["urgency_level"],
            suggested_timeline=assessment["suggested_timeline"],
            urgency_rationale=assessment["urgency_rationale"],
            recommended_specialist=assessment["recommended_specialist"],
            suggested_date=assessment["suggested_date"],
            status="suggested"
        )
        db.add(existing_followup)
        db.commit()
        db.refresh(existing_followup)

    return {
        "assessment": assessment,
        "followup_record_id": existing_followup.id,
        "followup_status": existing_followup.status,
        "patient_context": patient_context
    }

@router.get("/chronic-alerts")
def get_chronic_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns proactive AI alerts for chronic conditions based on patient history and latest vitals.
    """
    patient_context = {
        "full_name": current_user.full_name,
        "age": current_user.age or 45,
        "pre_existing_conditions": current_user.pre_existing_conditions or "",
        "drug_allergies": current_user.drug_allergies or ""
    }

    latest_readings = (
        db.query(IoTVitalReading)
        .filter(IoTVitalReading.patient_id == current_user.id)
        .order_by(IoTVitalReading.recorded_at.desc())
        .limit(10)
        .all()
    )
    vitals_list = [
        {
            "metric_type": r.metric_type,
            "primary_value": r.primary_value,
            "secondary_value": r.secondary_value,
            "recorded_at": r.recorded_at
        }
        for r in latest_readings
    ]

    generated_alerts = generate_chronic_ai_alerts(patient_context, vitals_list)

    # Persist active alerts to database if not present
    for a in generated_alerts:
        existing = (
            db.query(ChronicAlert)
            .filter(
                ChronicAlert.patient_id == current_user.id,
                ChronicAlert.alert_title == a["title"]
            )
            .first()
        )
        if not existing:
            new_alert = ChronicAlert(
                patient_id=current_user.id,
                condition_name=a["condition_name"],
                trigger_source="AI Multi-Factor Analysis",
                alert_title=a["title"],
                clinical_implication=a["clinical_implication"],
                recommended_action=a["recommended_action"],
                severity=a["severity"],
                is_active=True
            )
            db.add(new_alert)
    db.commit()

    db_alerts = (
        db.query(ChronicAlert)
        .filter(ChronicAlert.patient_id == current_user.id, ChronicAlert.is_active == True)
        .order_by(ChronicAlert.created_at.desc())
        .all()
    )

    return {
        "patient": current_user.full_name,
        "total_active_alerts": len(db_alerts),
        "alerts": [
            {
                "id": a.id,
                "condition_name": a.condition_name,
                "severity": a.severity,
                "alert_title": a.alert_title,
                "clinical_implication": a.clinical_implication,
                "recommended_action": a.recommended_action,
                "created_at": a.created_at
            }
            for a in db_alerts
        ]
    }

@router.post("/schedule-followup/{followup_id}")
def schedule_followup(
    followup_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Confirms the AI suggested predictive follow-up appointment slot.
    """
    f = db.query(PredictiveFollowUp).filter(
        PredictiveFollowUp.id == followup_id,
        PredictiveFollowUp.patient_id == current_user.id
    ).first()
    if not f:
        raise HTTPException(status_code=404, detail="Predictive follow-up record not found")

    f.status = "scheduled"
    db.commit()
    return {
        "message": f"Predictive follow-up successfully scheduled with {f.recommended_specialist} on {f.suggested_date}.",
        "status": "scheduled",
        "slot": f.suggested_date
    }
