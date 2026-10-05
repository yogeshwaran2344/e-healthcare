import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, MedicalReport
from ..schemas import (
    AdaptiveQuestionsRequest, AdaptiveQuestionsResponse,
    NavigatorAssessmentRequest, NavigatorAssessmentResponse
)
from ..auth import get_current_user
from ..ml.adaptive_engine import generate_adaptive_questions, compute_explainable_diagnosis

router = APIRouter(prefix="/api/navigator", tags=["AI Personal Health Navigator"])

@router.post("/questions", response_model=AdaptiveQuestionsResponse)
def get_adaptive_questions(
    req: AdaptiveQuestionsRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Dynamically generates targeted clinical follow-up questions
    tailored to the selected symptoms and patient age/history.
    """
    patient_context = {
        "age": current_user.age,
        "gender": current_user.gender,
        "pre_existing_conditions": current_user.pre_existing_conditions,
        "current_medications": current_user.current_medications
    }
    questions = generate_adaptive_questions(req.symptoms, patient_context)
    return AdaptiveQuestionsResponse(questions=questions)

@router.post("/assess", response_model=NavigatorAssessmentResponse)
def assess_multimodal_health(
    req: NavigatorAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Performs context-aware, multimodal AI health assessment:
    Combines reported symptoms + adaptive QA + patient medical profile + uploaded report biomarkers.
    Produces 3-tier triage level and Explainable AI (XAI) reasoning.
    """
    patient_context = {
        "age": current_user.age or 30,
        "gender": current_user.gender or "Not specified",
        "pre_existing_conditions": current_user.pre_existing_conditions or "",
        "current_medications": current_user.current_medications or "",
        "drug_allergies": current_user.drug_allergies or ""
    }

    # Aggregate extracted findings from uploaded reports if any
    biomarkers = {"abnormal_flags": [], "extracted_parameters": {}, "radiology_findings": []}
    if req.uploaded_report_ids:
        reports = db.query(MedicalReport).filter(
            MedicalReport.id.in_(req.uploaded_report_ids),
            MedicalReport.patient_id == current_user.id
        ).all()
        for r in reports:
            if r.extracted_findings:
                try:
                    f = json.loads(r.extracted_findings)
                    biomarkers["abnormal_flags"].extend(f.get("abnormal_flags", []))
                    biomarkers["extracted_parameters"].update(f.get("extracted_parameters", {}))
                    biomarkers["radiology_findings"].extend(f.get("radiology_findings", []))
                except Exception:
                    pass

    assessment = compute_explainable_diagnosis(
        symptoms=req.symptoms,
        qa_answers=req.qa_answers,
        patient_context=patient_context,
        biomarkers=biomarkers
    )

    return NavigatorAssessmentResponse(
        top_disease=assessment["top_disease"],
        confidence_percentage=assessment["confidence_percentage"],
        severity=assessment["severity"],
        specialist_recommended=assessment["specialist_recommended"],
        specialist_domain=assessment.get("specialist_domain", "Clinical Medicine"),
        specialist_rationale=assessment.get("specialist_rationale"),
        medical_advice=assessment["medical_advice"],
        recommended_diagnostic_tests=assessment["recommended_diagnostic_tests"],
        triage=assessment["triage"],
        xai_reasoning=assessment["xai_reasoning"],
        biomarkers_detected=biomarkers,
        other_possibilities=assessment["other_possibilities"],
        entropy_uncertainty=assessment.get("entropy_uncertainty"),
        explainable_decision_map=assessment.get("explainable_decision_map"),
        minimum_diagnostic_test_set=assessment.get("minimum_diagnostic_test_set")
    )
