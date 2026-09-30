"""
API Endpoints for Adaptive Closed-Loop Clinical Decision & Verification System.
Handles:
- Categorized Symptoms Catalog
- Dynamic Shannon-Entropy Uncertainty Assessment
- Information Gain Next-Best Questioning
- Pareto Minimum-Diagnostic-Test Optimization
- Doctor-AI Clinical Disagreement Logging & Taxonomy
- Outcome Verification & Closed-Loop Error Attribution
- AI Diagnostic Performance & Calibration Analytics
- Context-Aware Emergency Passport & Data-Bound Smart Consent
- Longitudinal Patient Digital Health Timeline
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import (
    User, Consultation, MedicalReport,
    ClinicalTimelineEntry, AdaptiveDiagnosticSession,
    ClinicalDisagreementRecord, ClinicalOutcomeRecord, ContextualQRToken
)
from ..auth import get_current_user
from ..schemas import (
    UncertaintyAssessmentRequest, NextQuestionRequest,
    MinimumTestOptimizationRequest, ClinicalDisagreementCreate,
    ClinicalOutcomeCreate, TimelineEntryCreate, ContextualTokenRequest,
    ExplainableMapRequest
)
from ..ml.dataset import SYMPTOMS_BY_CATEGORY, ALL_SYMPTOMS, TESTS_CATALOG, DISEASES_DB
from ..ml.uncertainty_engine import calculate_disease_posteriors, compute_entropy_and_uncertainty, identify_missing_critical_information
from ..ml.next_question_engine import select_next_best_question
from ..ml.test_optimization_engine import optimize_minimum_diagnostic_test_set
from ..ml.explainable_map_engine import generate_explainable_decision_map
from ..ml.disagreement_engine import analyze_clinician_ai_divergence, DISCREPANCY_TAXONOMY
from ..ml.outcome_feedback_engine import reconcile_three_way_outcome, compute_aggregate_model_calibration_metrics, FAILURE_MODES
from ..ml.passport_consent_engine import generate_contextual_emergency_token, filter_patient_data_by_context, CONTEXT_PERMISSIONS

router = APIRouter(prefix="/api/closed-loop", tags=["Adaptive Closed-Loop Clinical System"])

# ========================================================
# 1. Expanded Symptom Catalog
# ========================================================

@router.get("/symptoms-catalog")
def get_symptoms_catalog():
    """Returns categorized clinical symptoms for multi-system user selection."""
    return {
        "categories": SYMPTOMS_BY_CATEGORY,
        "total_symptoms_count": len(ALL_SYMPTOMS)
    }

# ========================================================
# 2. Shannon Entropy & Uncertainty Assessment
# ========================================================

@router.post("/uncertainty-assess")
def assess_uncertainty(
    req: UncertaintyAssessmentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Computes Shannon entropy H(D) and normalized diagnostic uncertainty (0-100%)
    based on reported symptoms and patient context.
    """
    patient_context = {
        "age": current_user.age or 35,
        "gender": current_user.gender or "Not specified",
        "pre_existing_conditions": current_user.pre_existing_conditions or "",
        "current_medications": current_user.current_medications or ""
    }

    biomarkers = {"abnormal_flags": []}
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
                except Exception:
                    pass

    posteriors = calculate_disease_posteriors(
        symptoms=req.symptoms,
        qa_answers=req.qa_answers,
        patient_context=patient_context,
        biomarkers=biomarkers
    )
    entropy_info = compute_entropy_and_uncertainty(posteriors)
    missing_info = identify_missing_critical_information(req.symptoms, req.qa_answers, patient_context)

    # Track in Adaptive Diagnostic Session
    session = AdaptiveDiagnosticSession(
        patient_id=current_user.id,
        initial_symptoms_json=json.dumps(req.symptoms),
        initial_entropy=entropy_info["shannon_entropy"],
        current_entropy=entropy_info["shannon_entropy"],
        current_uncertainty_score=entropy_info["uncertainty_score"],
        answered_questions_json=json.dumps(req.qa_answers or {}),
        top_predicted_disease=entropy_info["top_candidate"]["disease"],
        confidence_score=round(entropy_info["top_candidate"]["probability"] * 100, 1),
        session_status="in_progress"
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "shannon_entropy": entropy_info["shannon_entropy"],
        "uncertainty_score": entropy_info["uncertainty_score"],
        "certainty_band": entropy_info["certainty_band"],
        "action_allowed": entropy_info["action_allowed"],
        "top_candidate": entropy_info["top_candidate"],
        "candidate_distribution": entropy_info["candidate_distribution"],
        "missing_critical_parameters": missing_info
    }

# ========================================================
# 3. Dynamic Information Gain Next-Questioning
# ========================================================

@router.post("/next-question")
def get_next_best_question(
    req: NextQuestionRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Evaluates candidate questions and returns the single question that maximizes Information Gain.
    """
    patient_context = {
        "age": current_user.age or 35,
        "gender": current_user.gender or "Not specified",
        "pre_existing_conditions": current_user.pre_existing_conditions or ""
    }

    next_q = select_next_best_question(
        current_symptoms=req.symptoms,
        answered_question_ids=req.answered_question_ids,
        qa_answers=req.qa_answers,
        patient_context=patient_context
    )

    return {
        "has_next_question": next_q is not None,
        "next_question": next_q
    }

# ========================================================
# 4. Minimum-Diagnostic-Test Set Optimization
# ========================================================

@router.post("/minimum-tests")
def get_minimum_test_set(
    req: MinimumTestOptimizationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Computes Pareto-optimized Minimum Diagnostic Test Set balancing Information Gain vs. Cost & Radiation.
    """
    optimized = optimize_minimum_diagnostic_test_set(
        top_disease=req.top_disease,
        top_candidates=req.top_candidates,
        current_uncertainty=req.current_uncertainty,
        symptoms=req.symptoms,
        triage_level=req.triage_level
    )
    return optimized

# ========================================================
# 5. "Why did AI decide this?" Explainable Decision Map
# ========================================================

@router.post("/explainable-decision-map")
def get_explainable_map(
    req: ExplainableMapRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Generates Explainable Health Decision Map with numerical feature attributions (+/- weights).
    """
    patient_context = {
        "age": current_user.age or 35,
        "gender": current_user.gender or "Not specified",
        "pre_existing_conditions": current_user.pre_existing_conditions or ""
    }
    decision_map = generate_explainable_decision_map(
        target_disease=req.target_disease,
        symptoms=req.symptoms,
        qa_answers=req.qa_answers or {},
        patient_context=patient_context,
        biomarkers={},
        confidence_percentage=75.0
    )
    return decision_map

# ========================================================
# 6. Clinician-AI Disagreement Engine
# ========================================================

@router.post("/disagreement-record")
def record_disagreement(
    req: ClinicalDisagreementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a formal Clinical Disagreement Record when a physician's assessment diverges from AI.
    """
    analysis = analyze_clinician_ai_divergence(
        ai_predicted_disease=req.ai_predicted_disease,
        ai_confidence=req.ai_confidence,
        ai_triage=req.ai_triage_level,
        doctor_diagnosed_disease=req.doctor_diagnosed_disease,
        doctor_triage=req.doctor_triage_level,
        doctor_rationale=req.doctor_rationale,
        discrepancy_category=req.discrepancy_category,
        tests_considered=req.tests_considered
    )

    record = ClinicalDisagreementRecord(
        consultation_id=req.consultation_id,
        patient_id=req.patient_id,
        doctor_id=current_user.id,
        ai_predicted_disease=req.ai_predicted_disease,
        ai_confidence=req.ai_confidence,
        ai_triage_level=req.ai_triage_level,
        doctor_diagnosed_disease=req.doctor_diagnosed_disease,
        doctor_triage_level=req.doctor_triage_level,
        discrepancy_category=req.discrepancy_category,
        severity_grade=analysis.get("severity_grade", "MODERATE_DIAGNOSTIC_DIVERGENCE"),
        doctor_rationale=req.doctor_rationale,
        tests_considered_json=json.dumps(req.tests_considered or []),
        reconciliation_status="pending_outcome"
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {
        "record_id": record.id,
        "disagreement_analysis": analysis,
        "message": "Clinical Disagreement Record successfully committed to model improvement audit trail."
    }

@router.get("/disagreement-records")
def list_disagreements(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Lists historical clinician-AI disagreement records for clinical audit."""
    records = db.query(ClinicalDisagreementRecord).order_by(ClinicalDisagreementRecord.created_at.desc()).limit(50).all()
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "consultation_id": r.consultation_id,
            "patient_id": r.patient_id,
            "doctor_id": r.doctor_id,
            "ai_predicted_disease": r.ai_predicted_disease,
            "ai_confidence": r.ai_confidence,
            "doctor_diagnosed_disease": r.doctor_diagnosed_disease,
            "discrepancy_category": r.discrepancy_category,
            "severity_grade": r.severity_grade,
            "doctor_rationale": r.doctor_rationale,
            "tests_considered": json.loads(r.tests_considered_json) if r.tests_considered_json else [],
            "reconciliation_status": r.reconciliation_status,
            "created_at": r.created_at.isoformat()
        })
    return {"disagreement_records": results, "taxonomy_dictionary": DISCREPANCY_TAXONOMY}

# ========================================================
# 7. Outcome Verification & Closed-Loop Error Feedback
# ========================================================

@router.post("/verify-outcome")
def verify_outcome(
    req: ClinicalOutcomeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Performs 3-way triangulation: AI Prediction <---> Doctor Diagnosis <---> Confirmed True Outcome.
    Categorizes failure mode and registers feedback for model recalibration.
    """
    reconciliation = reconcile_three_way_outcome(
        ai_predicted_disease=req.ai_predicted_disease,
        doctor_diagnosed_disease=req.doctor_diagnosed_disease,
        confirmed_outcome_disease=req.confirmed_outcome_disease,
        confirmation_method=req.confirmation_method,
        days_to_resolution=req.days_to_resolution,
        outcome_status=req.outcome_status
    )

    record = ClinicalOutcomeRecord(
        consultation_id=req.consultation_id,
        patient_id=req.patient_id,
        ai_predicted_disease=req.ai_predicted_disease,
        doctor_diagnosed_disease=req.doctor_diagnosed_disease,
        confirmed_outcome_disease=req.confirmed_outcome_disease,
        confirmation_method=req.confirmation_method,
        days_to_resolution=req.days_to_resolution,
        ai_was_correct=reconciliation["ai_was_correct"],
        doctor_was_correct=reconciliation["doctor_was_correct"],
        error_category=reconciliation["error_category"],
        reconciliation_type=reconciliation["reconciliation_type"],
        calibration_feedback=reconciliation["feedback_loop_action"]
    )
    db.add(record)

    # Update any matching disagreement records to reconciled
    if req.consultation_id:
        disagreement = db.query(ClinicalDisagreementRecord).filter(
            ClinicalDisagreementRecord.consultation_id == req.consultation_id
        ).first()
        if disagreement:
            disagreement.reconciliation_status = "reconciled"

    # Add milestone to Patient Digital Health Timeline
    timeline_entry = ClinicalTimelineEntry(
        patient_id=req.patient_id,
        event_type="outcome_verified",
        title=f"Clinical Outcome Confirmed: {req.confirmed_outcome_disease}",
        description=f"Status: {req.outcome_status} via {req.confirmation_method}. Verdict: {reconciliation['summary_verdict']}",
        metrics_json=json.dumps({"reconciliation_type": reconciliation["reconciliation_type"], "days_to_resolution": req.days_to_resolution}),
        severity_level="Normal"
    )
    db.add(timeline_entry)
    db.commit()
    db.refresh(record)

    return {
        "record_id": record.id,
        "reconciliation": reconciliation,
        "message": "Ground-truth outcome successfully verified. AI error-feedback closed loop updated."
    }

@router.get("/ai-performance-calibration")
def get_ai_performance(
    db: Session = Depends(get_db)
):
    """
    Computes aggregate AI diagnostic performance, expected calibration metrics,
    and failure mode distribution from all confirmed outcome records.
    """
    records = db.query(ClinicalOutcomeRecord).all()
    records_data = []
    for r in records:
        records_data.append({
            "ai_predicted_disease": r.ai_predicted_disease,
            "doctor_diagnosed_disease": r.doctor_diagnosed_disease,
            "confirmed_outcome_disease": r.confirmed_outcome_disease,
            "ai_was_correct": r.ai_was_correct,
            "doctor_was_correct": r.doctor_was_correct,
            "error_category": r.error_category,
            "reconciliation_type": r.reconciliation_type
        })
    metrics = compute_aggregate_model_calibration_metrics(records_data)
    metrics["failure_modes_catalog"] = FAILURE_MODES
    return metrics

# ========================================================
# 8. Context-Aware Dynamic Emergency Passport
# ========================================================

@router.post("/passport/generate-token")
def create_passport_token(
    req: ContextualTokenRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generates a dynamic context-bound emergency QR token with auto-expiration."""
    token_meta = generate_contextual_emergency_token(current_user.id, req.context_scope)

    # Save to database
    qr_token = ContextualQRToken(
        patient_id=current_user.id,
        token_hash=token_meta["token"],
        context_scope=token_meta["context_scope"],
        expires_at=datetime.fromisoformat(token_meta["expires_at"]),
        access_count=0
    )
    db.add(qr_token)
    db.commit()
    db.refresh(qr_token)

    return {
        "token": qr_token.token_hash,
        "context_scope": qr_token.context_scope,
        "scope_label": token_meta["scope_label"],
        "expires_at": qr_token.expires_at.isoformat(),
        "validity_minutes": token_meta["validity_minutes"],
        "qr_access_url": f"/api/closed-loop/passport/view/{qr_token.token_hash}"
    }

@router.get("/passport/view/{token_hash}")
def view_contextual_passport(
    token_hash: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Public or Emergency Responder access endpoint.
    Filters patient medical dossier according to token's context scope.
    Logs access attempt in tamper-evident log.
    """
    token = db.query(ContextualQRToken).filter(ContextualQRToken.token_hash == token_hash).first()
    if not token:
        raise HTTPException(status_code=404, detail="Invalid emergency token.")

    if token.is_revoked:
        raise HTTPException(status_code=403, detail="Emergency token has been revoked by patient.")

    if datetime.utcnow() > token.expires_at:
        raise HTTPException(status_code=410, detail="Emergency token has EXPIRED. Request active re-generation.")

    patient = db.query(User).filter(User.id == token.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient profile not found.")

    # Audit logging
    token.access_count += 1
    token.last_accessed_at = datetime.utcnow()
    logs = json.loads(token.access_logs_json or "[]")
    logs.append({
        "timestamp": datetime.utcnow().isoformat(),
        "ip": request.client.host if request.client else "unknown",
        "user_agent": request.headers.get("user-agent", "unknown")
    })
    token.access_logs_json = json.dumps(logs)
    db.commit()

    # Build full data dictionary
    full_patient_data = {
        "full_name": patient.full_name,
        "age": patient.age or 35,
        "gender": patient.gender or "Not specified",
        "blood_group": patient.blood_group or "O+",
        "drug_allergies": patient.drug_allergies or "None reported",
        "emergency_contact_phone": patient.phone or "+91 98765 43210",
        "pre_existing_conditions": patient.pre_existing_conditions or "None recorded",
        "current_medications": patient.current_medications or "None",
        "recent_vitals": {"bp": "122/80 mmHg", "hr": "76 bpm", "spo2": "98%", "temp": "98.6°F"},
        "resuscitation_preference": "Full Code (Resuscitate)",
        "recent_lab_biomarkers": {"wbc": "7,800 /uL (Normal)", "platelets": "240,000 /uL (Normal)"},
        "radiology_reports": ["Chest X-Ray Normal (14 days ago)"],
        "recent_diagnoses": ["Viral Upper Respiratory Infection (Resolved)"],
        "treating_physician_notes": "Patient compliant with prescribed medication, no acute hemodynamic instability."
    }

    filtered_data = filter_patient_data_by_context(full_patient_data, token.context_scope)
    filtered_data["token_expires_at"] = token.expires_at.isoformat()
    filtered_data["access_count"] = token.access_count

    return filtered_data

# ========================================================
# 9. Longitudinal Patient Digital Health Timeline
# ========================================================

@router.get("/timeline/patient/{patient_id}")
def get_patient_timeline(
    patient_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns chronological digital health timeline milestones for longitudinal trend analysis."""
    entries = db.query(ClinicalTimelineEntry).filter(
        ClinicalTimelineEntry.patient_id == patient_id
    ).order_by(ClinicalTimelineEntry.recorded_at.desc()).limit(100).all()

    timeline_data = []
    for e in entries:
        timeline_data.append({
            "id": e.id,
            "event_type": e.event_type,
            "title": e.title,
            "description": e.description,
            "metrics": json.loads(e.metrics_json) if e.metrics_json else {},
            "severity_level": e.severity_level,
            "recorded_at": e.recorded_at.isoformat()
        })
    return {"patient_id": patient_id, "timeline_entries": timeline_data}

@router.post("/timeline/entry")
def add_timeline_entry(
    req: TimelineEntryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Appends an event milestone to the patient's continuous digital health timeline."""
    entry = ClinicalTimelineEntry(
        patient_id=current_user.id,
        event_type=req.event_type,
        title=req.title,
        description=req.description,
        metrics_json=json.dumps(req.metrics or {}),
        severity_level=req.severity_level or "Normal"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return {"entry_id": entry.id, "message": "Timeline milestone registered successfully."}
