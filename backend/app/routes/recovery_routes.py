from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Consultation, RecoveryCheckIn
from ..schemas import RecoveryCheckInCreate, RecoveryCheckInOut
from ..auth import get_current_user

router = APIRouter(prefix="/api/recovery", tags=["Recovery & Health Timeline"])

@router.post("", response_model=RecoveryCheckInOut)
def submit_recovery_checkin(
    req: RecoveryCheckInCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submits a post-consultation recovery status update (Day 1, 3, 7).
    Evaluates trajectory and gives automated AI feedback.
    """
    consultation = db.query(Consultation).filter(Consultation.id == req.consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation record not found.")

    if current_user.role == "patient" and consultation.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access.")

    # Determine intelligent AI feedback based on trajectory
    status_lower = req.symptom_status.lower()
    if "significantly improved" in status_lower or "cured" in status_lower:
        ai_feedback = "Excellent! Your recovery is progressing ahead of schedule. Complete the prescribed medicine course as advised."
    elif "improving" in status_lower:
        ai_feedback = "Recovery on track. Ensure adequate rest, hydration, and adhere to dosage timings."
    elif "worsened" in status_lower or "severe" in status_lower:
        ai_feedback = "CAUTION: Symptom progression indicates potential worsening or medication non-response. Re-consult your physician or seek in-person clinical review promptly."
    else:
        ai_feedback = "Symptoms static. Continue medications and monitor for 24-48 hours. Report to clinician if no improvement by Day 4."

    checkin = RecoveryCheckIn(
        consultation_id=consultation.id,
        patient_id=current_user.id,
        day_number=req.day_number,
        symptom_status=req.symptom_status,
        current_temperature=req.current_temperature,
        reported_symptoms=req.reported_symptoms,
        patient_notes=req.patient_notes,
        ai_feedback=ai_feedback
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)

    return checkin

@router.get("/{consultation_id}", response_model=List[RecoveryCheckInOut])
def get_recovery_timeline(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve longitudinal recovery check-in timeline for a consultation."""
    checkins = db.query(RecoveryCheckIn).filter(
        RecoveryCheckIn.consultation_id == consultation_id
    ).order_by(RecoveryCheckIn.day_number.asc()).all()
    return checkins
