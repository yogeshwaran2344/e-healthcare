"""
Explainable Health Decision Map Engine (XAI).
Generates fine-grained numerical positive/negative feature attributions (+/- weights),
evidence contribution breakdowns, and missing information impact.
"""

from typing import List, Dict, Any, Optional
from .dataset import DISEASES_DB, ALL_SYMPTOMS
from .uncertainty_engine import identify_missing_critical_information

def generate_explainable_decision_map(
    target_disease: str,
    symptoms: List[str],
    qa_answers: Optional[Dict[str, Any]] = None,
    patient_context: Optional[Dict[str, Any]] = None,
    biomarkers: Optional[Dict[str, Any]] = None,
    confidence_percentage: float = 75.0
) -> Dict[str, Any]:
    """
    Constructs the Explainable Health Decision Map:
    - Positive Evidence Weights (boosting condition probability)
    - Negative / Counter-Evidence Weights (reducing condition probability)
    - Missing Information with uncertainty penalties
    """
    qa_answers = qa_answers or {}
    patient_context = patient_context or {}
    biomarkers = biomarkers or {}

    d_info = DISEASES_DB.get(target_disease, {})
    d_symptoms = set(d_info.get("symptoms", []))
    input_syms = set(symptoms)

    positive_factors = []
    negative_factors = []

    # 1. Symptom Attributions
    matched_symptoms = input_syms & d_symptoms
    for sym in matched_symptoms:
        readable = sym.replace("_", " ").title()
        # Hallmark symptoms carry higher weight
        if any(h in sym for h in ["sharp_chest_pain", "facial_droop", "petechiae", "shortness_of_breath", "high_fever"]):
            weight = +24
        else:
            weight = +16
        positive_factors.append({
            "feature": f"Observed Symptom: {readable}",
            "weight": weight,
            "category": "Reported Clinical Symptom",
            "effect": "Strongly Elevates Probability"
        })

    # Unmatched symptoms that argue against or point elsewhere
    unmatched_symptoms = input_syms - d_symptoms
    for u_sym in list(unmatched_symptoms)[:3]:
        readable = u_sym.replace("_", " ").title()
        negative_factors.append({
            "feature": f"Discordant Symptom: {readable}",
            "weight": -8,
            "category": "Alternative Etiology Indicator",
            "effect": "Modestly Reduces Specificity"
        })

    # Absence of key disease symptoms
    missing_from_disease = d_symptoms - input_syms
    if len(missing_from_disease) > 2 and len(input_syms) >= 4:
        key_missing = list(missing_from_disease)[0].replace("_", " ").title()
        negative_factors.append({
            "feature": f"Absence of classic finding: {key_missing}",
            "weight": -12,
            "category": "Pertinent Negative",
            "effect": "Inhibits Definitive Diagnostic Certainty"
        })

    # 2. Patient Profile & History Attributions
    pre_existing = str(patient_context.get("pre_existing_conditions", "")).lower()
    age = patient_context.get("age", 30) or 30

    if "cardiac" in target_disease.lower() or "angina" in target_disease.lower():
        if "hypertension" in pre_existing or "heart" in pre_existing:
            positive_factors.append({
                "feature": "Documented Pre-existing Cardiovascular History",
                "weight": +22,
                "category": "Patient Comorbidity Risk Factor",
                "effect": "Substantially Increases Prior Probability"
            })
        if age >= 50:
            positive_factors.append({
                "feature": f"Patient Age ({age} yrs) Demographic Risk",
                "weight": +14,
                "category": "Demographic Profile",
                "effect": "Elevates Vulnerability Window"
            })

    if "pneumonia" in target_disease.lower() or "covid" in target_disease.lower():
        if "diabetes" in pre_existing or "asthma" in pre_existing:
            positive_factors.append({
                "feature": "Pre-existing Respiratory/Metabolic Vulnerability",
                "weight": +18,
                "category": "Immune & Pulmonary Risk",
                "effect": "Elevates Lower Respiratory Susceptibility"
            })

    # 3. Biomarker Lab Attributions
    abnormal_flags = biomarkers.get("abnormal_flags", [])
    for ab in abnormal_flags:
        if "Platelet" in ab and "dengue" in target_disease.lower():
            positive_factors.append({
                "feature": f"Lab Finding: {ab}",
                "weight": +28,
                "category": "Objective Biomarker Finding",
                "effect": "High Diagnostic Specificity"
            })
        elif "WBC" in ab and ("pneumonia" in target_disease.lower() or "typhoid" in target_disease.lower()):
            positive_factors.append({
                "feature": f"Lab Finding: {ab}",
                "weight": +22,
                "category": "Objective Biomarker Finding",
                "effect": "Confirms Acute Bacterial Infection"
            })
        elif "Troponin" in ab and "cardiac" in target_disease.lower():
            positive_factors.append({
                "feature": f"Lab Finding: {ab}",
                "weight": +35,
                "category": "Objective Biomarker Finding",
                "effect": "Critical Myocardial Injury Marker"
            })

    # 4. Missing Clinical Parameters
    missing_info = identify_missing_critical_information(symptoms, qa_answers, patient_context)

    # Calculate net attribution sum
    net_positive = sum(f["weight"] for f in positive_factors)
    net_negative = sum(f["weight"] for f in negative_factors)

    return {
        "target_disease": target_disease,
        "calibrated_confidence": round(confidence_percentage, 1),
        "net_positive_score": net_positive,
        "net_negative_score": net_negative,
        "positive_attributions": positive_factors,
        "negative_attributions": negative_factors,
        "missing_information_penalties": missing_info,
        "interpretability_narrative": f"Diagnosis of '{target_disease}' is driven by {len(positive_factors)} primary clinical features (net +{net_positive}), counterbalanced by {len(negative_factors)} divergent factors (net {net_negative})."
    }
