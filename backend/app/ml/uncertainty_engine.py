"""
Uncertainty & Shannon Entropy Engine for Adaptive Clinical Decision Making.
Computes posterior disease probability distribution, Shannon entropy H(D),
normalized diagnostic uncertainty score (0-100%), and identifies critical missing data.
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import DISEASES_DB, ALL_SYMPTOMS

def calculate_disease_posteriors(
    symptoms: List[str],
    qa_answers: Optional[Dict[str, Any]] = None,
    patient_context: Optional[Dict[str, Any]] = None,
    biomarkers: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Computes normalized posterior probabilities across all diseases
    given observed symptoms, patient risk factors, and lab biomarkers.
    """
    qa_answers = qa_answers or {}
    patient_context = patient_context or {}
    biomarkers = biomarkers or {}
    
    input_syms = set(symptoms)
    raw_scores = {}
    
    pre_existing_str = str(patient_context.get("pre_existing_conditions", "")).lower()
    age = patient_context.get("age", 35) or 35
    abnormal_biomarkers = " ".join(biomarkers.get("abnormal_flags", [])).lower()

    for d_name, d_info in DISEASES_DB.items():
        d_syms = set(d_info["symptoms"])
        matched = input_syms & d_syms
        
        # Jaccard + Recall weighted match
        precision = len(matched) / len(input_syms) if input_syms else 0.0
        recall = len(matched) / len(d_syms) if d_syms else 0.0
        base_evidence = (0.6 * recall) + (0.4 * precision)

        # Baseline smoothing epsilon
        score = base_evidence + 0.02
        
        # Risk factor boosters
        if "cardiac" in d_name.lower() or "angina" in d_name.lower():
            if age >= 55:
                score += 0.15
            if "hypertension" in pre_existing_str or "heart" in pre_existing_str or "diabetes" in pre_existing_str:
                score += 0.20
            if "troponin" in abnormal_biomarkers or "ecg" in abnormal_biomarkers:
                score += 0.50
        
        if "stroke" in d_name.lower():
            if "hypertension" in pre_existing_str or age >= 60:
                score += 0.20
                
        if "pneumonia" in d_name.lower():
            if "diabetes" in pre_existing_str or "copd" in pre_existing_str or "asthma" in pre_existing_str:
                score += 0.15
            if "infiltrate" in abnormal_biomarkers or "wbc" in abnormal_biomarkers:
                score += 0.40

        if "dengue" in d_name.lower():
            if "platelet" in abnormal_biomarkers or "ns1" in abnormal_biomarkers:
                score += 0.50

        # Penalize if major hallmark symptom is missing when many symptoms are provided
        if len(input_syms) >= 4 and len(matched) == 0:
            score = 0.005

        raw_scores[d_name] = max(score, 0.005)

    # Softmax / Normalize to probability distribution
    total = sum(raw_scores.values())
    posteriors = {k: v / total for k, v in raw_scores.items()}
    return posteriors

def compute_entropy_and_uncertainty(posteriors: Dict[str, float]) -> Dict[str, Any]:
    """
    Computes Shannon Entropy H(D) = - sum(p * log2(p)).
    Normalizes entropy against theoretical maximum H_max = log2(N_diseases).
    Returns uncertainty score (0-100%) and decision state.
    """
    n = len(posteriors)
    if n <= 1:
        return {"entropy": 0.0, "uncertainty_score": 0.0, "status": "Definitive"}

    entropy = -sum(p * math.log2(p) for p in posteriors.values() if p > 0)
    max_entropy = math.log2(n)
    
    # Normalized Uncertainty Index in [0.0, 1.0]
    normalized_uncertainty = min(max(entropy / max_entropy, 0.0), 1.0)
    uncertainty_percentage = round(normalized_uncertainty * 100, 1)

    # Categorize clinical certainty
    if uncertainty_percentage <= 25.0:
        certainty_band = "High Certainty (Ready for Clinical Action)"
        action_allowed = True
    elif uncertainty_percentage <= 60.0:
        certainty_band = "Moderate Uncertainty (Targeted Inquiry / Lab Test Needed)"
        action_allowed = False
    else:
        certainty_band = "High Uncertainty (Adaptive Clarification Required)"
        action_allowed = False

    # Top candidates
    sorted_candidates = sorted(posteriors.items(), key=lambda x: x[1], reverse=True)
    top_candidate = sorted_candidates[0]
    margin_to_second = (top_candidate[1] - sorted_candidates[1][1]) if len(sorted_candidates) > 1 else 1.0

    return {
        "shannon_entropy": round(entropy, 3),
        "max_theoretical_entropy": round(max_entropy, 3),
        "uncertainty_score": uncertainty_percentage,
        "certainty_band": certainty_band,
        "action_allowed": action_allowed,
        "top_candidate": {
            "disease": top_candidate[0],
            "probability": round(top_candidate[1], 3),
            "margin_over_runner_up": round(margin_to_second, 3)
        },
        "candidate_distribution": [
            {"disease": d, "probability": round(p, 4), "percentage": round(p * 100, 1)}
            for d, p in sorted_candidates[:5]
        ]
    }

def identify_missing_critical_information(
    symptoms: List[str],
    qa_answers: Optional[Dict[str, Any]] = None,
    patient_context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, str]]:
    """
    Identifies specific missing clinical parameters that prevent diagnostic convergence.
    """
    qa_answers = qa_answers or {}
    patient_context = patient_context or {}
    missing = []

    symptoms_set = set(symptoms)

    # Check temporal parameter
    if "duration_days" not in qa_answers:
        missing.append({
            "parameter": "Symptom Onset & Duration",
            "impact": "Distinguishes acute emergency vs chronic insidious process",
            "criticality": "High"
        })

    # Check pain severity
    if any(s in symptoms_set for s in ["sharp_chest_pain", "abdominal_pain", "severe_headache", "flank_kidney_angle_pain"]):
        if "severity_scale" not in qa_answers:
            missing.append({
                "parameter": "Quantitative Pain Scale (1-10)",
                "impact": "Required to calibrate emergency triage escalation",
                "criticality": "High"
            })

    # Check cardiac radiation
    if "sharp_chest_pain" in symptoms_set and "pain_radiating_to_arm_jaw" not in symptoms_set and "radiation_inquired" not in qa_answers:
        missing.append({
            "parameter": "Pain Radiation (Left Arm, Neck, Jaw)",
            "impact": "Hallmark differentiator for acute myocardial infarction",
            "criticality": "Critical"
        })

    # Check fever curve & chills
    if any("fever" in s for s in symptoms_set) and "fever_profile" not in qa_answers:
        missing.append({
            "parameter": "Fever Temperature Curve & Rigors",
            "impact": "Differentiates viral intermittent vs typhoid step-ladder vs bacterial spike",
            "criticality": "Medium"
        })

    # Check prior medication
    if "prior_meds_taken" not in qa_answers:
        missing.append({
            "parameter": "Recent Over-The-Counter Medication Use",
            "impact": "Identifies masking of fever/pain and drug-induced gastric symptoms",
            "criticality": "Medium"
        })

    return missing
