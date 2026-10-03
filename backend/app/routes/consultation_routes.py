import json
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, Consultation, MedicalReport, Prescription, RecoveryCheckIn
from ..schemas import (
    ConsultationCreate, ConsultationOut, MedicalReportOut,
    PrescriptionOut, MedicineItem, RecoveryCheckInOut
)
from ..auth import get_current_user
from ..ml.handover_engine import generate_sbar_handover

router = APIRouter(prefix="/api/consultations", tags=["Consultations & Clinical Handover"])

def format_consultation_out(c: Consultation, db: Session) -> ConsultationOut:
    patient = db.query(User).filter(User.id == c.patient_id).first()
    doctor = db.query(User).filter(User.id == c.doctor_id).first() if c.doctor_id else None

    # Parse symptoms
    symptoms = []
    if c.symptoms_list:
        try:
            symptoms = json.loads(c.symptoms_list)
        except Exception:
            symptoms = [s.strip() for s in c.symptoms_list.split(",") if s.strip()]

    # Format reports
    reports_out = []
    for r in c.reports:
        findings = None
        if r.extracted_findings:
            try:
                findings = json.loads(r.extracted_findings)
            except Exception:
                pass
        reports_out.append(MedicalReportOut(
            id=r.id,
            consultation_id=r.consultation_id,
            patient_id=r.patient_id,
            report_type=r.report_type,
            original_filename=r.original_filename,
            stored_filename=r.stored_filename,
            file_url=f"/api/reports/{r.id}/file",
            extracted_findings=findings,
            uploaded_at=r.uploaded_at
        ))

    # Format prescription if exists
    presc_out = None
    if c.prescription:
        p = c.prescription
        p_doctor = db.query(User).filter(User.id == p.doctor_id).first()
        medicines = []
        if p.medicines_json:
            try:
                raw_m = json.loads(p.medicines_json)
                medicines = [MedicineItem(**m) for m in raw_m]
            except Exception:
                pass
        safety_alerts = None
        if p.safety_alerts:
            try:
                safety_alerts = json.loads(p.safety_alerts)
            except Exception:
                pass

        presc_out = PrescriptionOut(
            id=p.id,
            consultation_id=p.consultation_id,
            doctor_id=p.doctor_id,
            doctor_name=p_doctor.full_name if p_doctor else "Attending Doctor",
            diagnosis=p.diagnosis,
            medicines=medicines,
            general_advice=p.general_advice,
            follow_up_days=p.follow_up_days,
            safety_alerts=safety_alerts,
            created_at=p.created_at
        )

    # Format Recovery Check-ins
    recovery_out = []
    for rc in c.recovery_checkins:
        recovery_out.append(RecoveryCheckInOut(
            id=rc.id,
            consultation_id=rc.consultation_id,
            patient_id=rc.patient_id,
            day_number=rc.day_number,
            symptom_status=rc.symptom_status,
            current_temperature=rc.current_temperature,
            reported_symptoms=rc.reported_symptoms,
            patient_notes=rc.patient_notes,
            ai_feedback=rc.ai_feedback,
            created_at=rc.created_at
        ))

    # Parse JSON fields
    qa_dict = json.loads(c.adaptive_qa) if c.adaptive_qa else None
    bio_dict = json.loads(c.extracted_biomarkers) if c.extracted_biomarkers else None
    xai_list = json.loads(c.xai_reasoning) if c.xai_reasoning else None
    handover_dict = json.loads(c.clinical_handover_summary) if c.clinical_handover_summary else None

    return ConsultationOut(
        id=c.id,
        patient_id=c.patient_id,
        patient_name=patient.full_name if patient else "Patient",
        patient_email=patient.email if patient else "",
        patient_phone=patient.phone if patient else "",
        patient_age=patient.age if patient else None,
        patient_gender=patient.gender if patient else None,
        patient_allergies=patient.drug_allergies if patient else None,
        patient_conditions=patient.pre_existing_conditions if patient else None,
        doctor_id=c.doctor_id,
        doctor_name=doctor.full_name if doctor else "Pending Doctor Assignment",
        symptoms_list=symptoms,
        predicted_disease=c.predicted_disease,
        confidence_score=c.confidence_score,
        recommended_tests=c.recommended_tests,
        severity=c.severity,
        triage_level=c.triage_level,
        adaptive_qa=qa_dict,
        extracted_biomarkers=bio_dict,
        xai_reasoning=xai_list,
        clinical_handover_summary=handover_dict,
        patient_notes=c.patient_notes,
        status=c.status,
        created_at=c.created_at,
        reports=reports_out,
        prescription=presc_out,
        recovery_checkins=recovery_out
    )

@router.post("", response_model=ConsultationOut)
def create_consultation(
    req: ConsultationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Only patients can book consultations.")

    symptoms_json = json.dumps(req.symptoms)
    qa_json = json.dumps(req.adaptive_qa or {})
    bio_json = json.dumps(req.extracted_biomarkers or {})
    xai_json = json.dumps(req.xai_reasoning or [])

    # Synthesize AI Clinical Handover (SBAR) for the doctor
    patient_info = {
        "full_name": current_user.full_name,
        "age": current_user.age,
        "gender": current_user.gender,
        "pre_existing_conditions": current_user.pre_existing_conditions,
        "current_medications": current_user.current_medications,
        "drug_allergies": current_user.drug_allergies
    }
    triage_info = {"triage_level": req.triage_level or "Doctor Consultation"}
    
    handover = generate_sbar_handover(
        patient_info=patient_info,
        symptoms=req.symptoms,
        qa_answers=req.adaptive_qa or {},
        predicted_disease=req.predicted_disease or "General Consultation",
        confidence=req.confidence_score or 0.0,
        triage_data=triage_info,
        biomarkers=req.extracted_biomarkers or {},
        patient_notes=req.patient_notes or ""
    )
    handover_json = json.dumps(handover)

    consultation = Consultation(
        patient_id=current_user.id,
        doctor_id=req.doctor_id,
        symptoms_list=symptoms_json,
        predicted_disease=req.predicted_disease,
        confidence_score=req.confidence_score or 0.0,
        recommended_tests=req.recommended_tests,
        severity=req.severity or "Moderate",
        triage_level=req.triage_level or "Doctor Consultation",
        adaptive_qa=qa_json,
        extracted_biomarkers=bio_json,
        xai_reasoning=xai_json,
        clinical_handover_summary=handover_json,
        patient_notes=req.patient_notes,
        status="pending"
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    return format_consultation_out(consultation, db)

@router.get("", response_model=List[ConsultationOut])
def list_consultations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "patient":
        consultations = db.query(Consultation).filter(
            Consultation.patient_id == current_user.id
        ).order_by(Consultation.created_at.desc()).all()
    elif current_user.role == "doctor":
        consultations = db.query(Consultation).filter(
            (Consultation.doctor_id == current_user.id) | (Consultation.doctor_id == None)
        ).order_by(Consultation.created_at.desc()).all()
    else:
        consultations = db.query(Consultation).order_by(Consultation.created_at.desc()).all()

    return [format_consultation_out(c, db) for c in consultations]

from ..consent_service import enforce_patient_consent_or_emergency

@router.get("/{consultation_id}", response_model=ConsultationOut)
def get_consultation(
    consultation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
    if not consultation:
        raise HTTPException(status_code=404, detail="Consultation not found.")

    if current_user.role == "patient" and consultation.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied.")

    if current_user.role == "doctor" and consultation.patient_id != current_user.id:
        # Check if doctor is the directly assigned doctor
        if consultation.doctor_id != current_user.id:
            enforce_patient_consent_or_emergency(
                db, consultation.patient_id, current_user, "diagnoses", purpose=f"Clinical review of consultation #{consultation_id}"
            )

    return format_consultation_out(consultation, db)
