import os
import uuid
import json
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, MedicalReport, Consultation
from ..schemas import MedicalReportOut
from ..auth import get_current_user
from ..config import UPLOAD_DIR
from ..ml.report_intelligence import process_uploaded_file_intelligence

router = APIRouter(prefix="/api/reports", tags=["Medical Reports & Biomarker Extraction"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf", ".webp", ".txt"}

@router.post("/upload", response_model=MedicalReportOut)
async def upload_medical_report(
    report_type: str = Form(...),
    consultation_id: int = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload an image or document of a medical test report / scan.
    Automatically extracts biomarkers, out-of-range flags, and clinical parameters.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' not allowed. Please upload JPG, PNG, or PDF files."
        )

    # Validate consultation if provided
    consultation = None
    if consultation_id:
        consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
        if not consultation:
            raise HTTPException(status_code=404, detail="Consultation not found.")
        if current_user.role == "patient" and consultation.patient_id != current_user.id:
            raise HTTPException(status_code=403, detail="Unauthorized consultation access.")

    # Unique stored filename
    unique_name = f"{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(UPLOAD_DIR, unique_name)

    content = await file.read()
    with open(dest_path, "wb") as f:
        f.write(content)

    # Run automated AI biomarker extraction
    intelligence = process_uploaded_file_intelligence(dest_path, report_type)
    intelligence_json = json.dumps(intelligence)

    report = MedicalReport(
        consultation_id=consultation_id,
        patient_id=current_user.id,
        report_type=report_type,
        original_filename=file.filename,
        stored_filename=unique_name,
        file_path=dest_path,
        extracted_findings=intelligence_json
    )
    db.add(report)

    # If linked to a consultation, update consultation's extracted biomarkers summary
    if consultation:
        existing_bio = {}
        if consultation.extracted_biomarkers:
            try:
                existing_bio = json.loads(consultation.extracted_biomarkers)
            except Exception:
                pass
        
        abnormal = existing_bio.get("abnormal_flags", [])
        abnormal.extend(intelligence.get("abnormal_flags", []))
        existing_bio["abnormal_flags"] = list(set(abnormal))
        
        params = existing_bio.get("extracted_parameters", {})
        params.update(intelligence.get("extracted_parameters", {}))
        existing_bio["extracted_parameters"] = params
        
        consultation.extracted_biomarkers = json.dumps(existing_bio)

    db.commit()
    db.refresh(report)

    return MedicalReportOut(
        id=report.id,
        consultation_id=report.consultation_id,
        patient_id=report.patient_id,
        report_type=report.report_type,
        original_filename=report.original_filename,
        stored_filename=report.stored_filename,
        file_url=f"/api/reports/{report.id}/file",
        extracted_findings=intelligence,
        uploaded_at=report.uploaded_at
    )

from ..consent_service import enforce_patient_consent_or_emergency

@router.get("/{report_id}/file")
def get_report_file(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Serve the uploaded medical scan or lab report image/document with strict access control."""
    report = db.query(MedicalReport).filter(MedicalReport.id == report_id).first()
    if not report or not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="Medical report file not found.")

    # Prevent path traversal
    real_path = os.path.realpath(report.file_path)
    real_upload = os.path.realpath(UPLOAD_DIR)
    if not real_path.startswith(real_upload):
        raise HTTPException(status_code=403, detail="Illegal file path access.")

    # Authorization & Consent Check
    if current_user.role == "patient" and report.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to patient report.")

    if current_user.role == "doctor" and report.patient_id != current_user.id:
        enforce_patient_consent_or_emergency(
            db, report.patient_id, current_user, "labs", purpose=f"Viewing lab report #{report_id} document"
        )

    ext = os.path.splitext(report.file_path)[1].lower()
    media_type = "application/pdf" if ext == ".pdf" else f"image/{ext.replace('.', '')}"
    return FileResponse(report.file_path, media_type=media_type, filename=report.original_filename)
