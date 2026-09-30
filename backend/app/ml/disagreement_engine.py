"""
Clinician-AI Clinical Disagreement & Divergence Engine.
Detects, records, and categorizes diagnostic and triage divergence between AI models
and reviewing physicians to power closed-loop learning and safety audits.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

# Discrepancy Taxonomy Categories
DISCREPANCY_TAXONOMY = {
    "ATYPICAL_PRESENTATION": "Patient exhibited non-canonical symptoms (e.g., epigastric distress in inferior wall MI).",
    "PHYSICAL_EXAM_OVERRIDE": "Clinician observed bedside physical exam signs (e.g., lung rales, focal neurological signs, Murphy's sign) absent in questionnaire.",
    "EPIDEMIOLOGICAL_CONTEXT": "Doctor incorporated local outbreak prevalence (e.g., seasonal Dengue surge) not captured in default priors.",
    "RISK_AVERSION_SAFETY_UPGRADE": "Clinician upgraded triage level to Emergency to safeguard against catastrophic occult deterioration.",
    "LAB_IMAGING_DISCORDANCE": "Uploaded imaging or biomarker report directly contradicted symptom-only heuristic.",
    "INCOMPLETE_SYMPTOM_CAPTURE": "Patient communicated critical symptom verbally during consultation that was omitted during initial digital intake."
}

def analyze_clinician_ai_divergence(
    ai_predicted_disease: str,
    ai_confidence: float,
    ai_triage: str,
    doctor_diagnosed_disease: str,
    doctor_triage: Optional[str] = None,
    doctor_rationale: Optional[str] = None,
    discrepancy_category: Optional[str] = None,
    tests_considered: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluates whether clinician decision diverges from AI recommendation.
    If divergent, classifies severity of divergence and builds structured disagreement payload.
    """
    doctor_triage = doctor_triage or ai_triage
    tests_considered = tests_considered or []
    
    is_disease_divergent = (ai_predicted_disease.strip().lower() != doctor_diagnosed_disease.strip().lower())
    is_triage_divergent = (ai_triage.strip().lower() != doctor_triage.strip().lower())
    
    has_disagreement = is_disease_divergent or is_triage_divergent
    
    if not has_disagreement:
        return {
            "has_disagreement": False,
            "status": "CONCORDANT",
            "message": "Doctor diagnosis and triage level are in complete concordance with AI prediction."
        }

    # Determine Divergence Severity
    if is_triage_divergent and "Emergency" in doctor_triage and "Emergency" not in ai_triage:
        severity_grade = "CRITICAL_SAFETY_DIVERGENCE"
        audit_urgency = "Immediate Sentinel Review"
    elif is_disease_divergent and ("cardiac" in ai_predicted_disease.lower() or "cardiac" in doctor_diagnosed_disease.lower() or "stroke" in doctor_diagnosed_disease.lower()):
        severity_grade = "HIGH_CLINICAL_DIVERGENCE"
        audit_urgency = "Priority Safety Review"
    elif is_disease_divergent:
        severity_grade = "MODERATE_DIAGNOSTIC_DIVERGENCE"
        audit_urgency = "Standard Model Calibration Review"
    else:
        severity_grade = "LOW_TRIAGE_REFINEMENT"
        audit_urgency = "Routine Calibration"

    category = discrepancy_category if discrepancy_category in DISCREPANCY_TAXONOMY else "PHYSICAL_EXAM_OVERRIDE"
    category_description = DISCREPANCY_TAXONOMY[category]

    return {
        "has_disagreement": True,
        "status": "DIVERGENT",
        "severity_grade": severity_grade,
        "audit_urgency": audit_urgency,
        "ai_prediction": {
            "disease": ai_predicted_disease,
            "confidence": round(ai_confidence, 1),
            "triage_level": ai_triage
        },
        "doctor_assessment": {
            "disease": doctor_diagnosed_disease,
            "triage_level": doctor_triage,
            "clinical_rationale": doctor_rationale or "Clinical evaluation revealed findings contrary to automated intake.",
            "discrepancy_category": category,
            "category_description": category_description,
            "tests_ordered_for_differential": tests_considered
        },
        "reconciliation_required": True,
        "recorded_at": datetime.utcnow().isoformat()
    }
