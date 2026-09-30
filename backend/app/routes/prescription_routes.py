import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Consultation, Prescription
from ..schemas import PrescriptionCreate, PrescriptionOut, MedicineItem, SafetyCheckRequest
from ..auth import get_current_user
from ..ml.safety_engine import check_medication_safety

router = APIRouter(prefix="/api/prescriptions", tags=["Prescriptions & Drug Safety"])

@router.post("/safety-check")
def precheck_safety(
    req: SafetyCheckRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Live safety checker for doctors: cross-checks candidate medications
    against patient allergies and chronic medical conditions.
    """
    consultation = db.query(Consultation).filter(Consultation.id == req.consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found.")

    patient = db.query(User).filter(User.id == consultation.patient_id).first()
    medicines_data = [m.model_dump() for m in req.medicines]

    safety_result = check_medication_safety(
        prescribed_medicines=medicines_data,
        patient_allergies_str=patient.drug_allergies or "",
        patient_conditions_str=patient.pre_existing_conditions or ""
    )
    return safety_result

@router.post("", response_model=PrescriptionOut)
def create_prescription(
    req: PrescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allows a doctor to issue a digital prescription with integrated safety validation."""
    if current_user.role != "doctor":
        raise HTTPException(status_code=403, detail="Only verified doctors can issue prescriptions.")

    consultation = db.query(Consultation).filter(Consultation.id == req.consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found.")

    # Check if a prescription already exists
    existing = db.query(Prescription).filter(Prescription.consultation_id == req.consultation_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="A prescription has already been issued for this consultation.")

    # Validate drug safety against patient allergies
    patient = db.query(User).filter(User.id == consultation.patient_id).first()
    medicines_data = [m.model_dump() for m in req.medicines]
    safety_result = check_medication_safety(
        prescribed_medicines=medicines_data,
        patient_allergies_str=patient.drug_allergies or "",
        patient_conditions_str=patient.pre_existing_conditions or ""
    )

    medicines_str = json.dumps(medicines_data)
    safety_json = json.dumps(safety_result)

    prescription = Prescription(
        consultation_id=consultation.id,
        doctor_id=current_user.id,
        diagnosis=req.diagnosis,
        medicines_json=medicines_str,
        general_advice=req.general_advice,
        follow_up_days=req.follow_up_days or 7,
        safety_alerts=safety_json
    )
    db.add(prescription)

    # Update consultation status
    consultation.status = "completed"
    if not consultation.doctor_id:
        consultation.doctor_id = current_user.id

    db.commit()
    db.refresh(prescription)

    return PrescriptionOut(
        id=prescription.id,
        consultation_id=prescription.consultation_id,
        doctor_id=prescription.doctor_id,
        doctor_name=current_user.full_name,
        diagnosis=prescription.diagnosis,
        medicines=req.medicines,
        general_advice=prescription.general_advice,
        follow_up_days=prescription.follow_up_days,
        safety_alerts=safety_result,
        created_at=prescription.created_at
    )

@router.get("/{prescription_id}", response_model=PrescriptionOut)
def get_prescription(
    prescription_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve full prescription details including medication safety verification."""
    p = db.query(Prescription).filter(Prescription.id == prescription_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Prescription not found.")

    doctor = db.query(User).filter(User.id == p.doctor_id).first()
    medicines_raw = json.loads(p.medicines_json) if p.medicines_json else []
    medicines_objs = [MedicineItem(**m) for m in medicines_raw]
    safety_data = json.loads(p.safety_alerts) if p.safety_alerts else None

    return PrescriptionOut(
        id=p.id,
        consultation_id=p.consultation_id,
        doctor_id=p.doctor_id,
        doctor_name=doctor.full_name if doctor else "Attending Doctor",
        diagnosis=p.diagnosis,
        medicines=medicines_objs,
        general_advice=p.general_advice,
        follow_up_days=p.follow_up_days,
        safety_alerts=safety_data,
        created_at=p.created_at
    )
