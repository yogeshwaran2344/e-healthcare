"""
Uncertainty & Shannon Entropy Engine for Adaptive Clinical Decision Making.
Computes posterior disease probability distribution, Shannon entropy H(D),
normalized diagnostic uncertainty score (0-100%), and identifies critical missing data.
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import DISEASES_DB, ALL_SYMPTOMS

SYMPTOM_CLUSTERS = {
    "chest_pain": ["chest", "pain", "angina", "discomfort", "tightness", "pressure", "retrosternal", "heart"],
    "sweating": ["sweat", "sweating", "diaphoresis", "clammy", "cold"],
    "arm_radiation": ["radiation", "radiating", "arm", "jaw", "neck", "shoulder"],
    "fever": ["fever", "pyrexia", "temperature", "chills", "feverish", "shivering"],
    "cough": ["cough", "coughing", "phlegm", "sputum", "bronchial", "hack"],
    "sputum": ["sputum", "phlegm", "mucus", "productive", "yellow", "green"],
    "breathlessness": ["breath", "breathlessness", "dyspnea", "shortness", "wheezing", "stridor"],
    "headache": ["headache", "migraine", "throbbing", "head", "cranial"],
    "body_pain": ["body", "muscle", "aches", "ache", "myalgia", "fatigue", "tired", "weakness", "malaise"],
    "abdominal": ["abdominal", "stomach", "belly", "tummy", "epigastric", "cramps"],
    "jaundice": ["jaundice", "yellowing", "yellow", "sclera", "icterus"],
    "vomiting": ["vomit", "vomiting", "emesis", "nausea", "queasy"],
    "hair_scalp": ["hair", "scalp", "fall", "shedding", "thinning", "dandruff", "alopecia", "flaking", "folliculitis"],
    "acne_skin": ["acne", "pimples", "pimple", "breakout", "blackhead", "whitehead", "comedone", "sebum", "skin", "rash", "spots"],
    "gynac_period": ["period", "periods", "menstrual", "cramps", "dysmenorrhea", "bleeding", "pcos", "pcod", "ovarian", "pelvic", "vaginal", "discharge"],
    "urinary": ["urine", "urination", "dysuria", "burning", "frequency", "kidney", "flank", "hematuria"]
}

def match_symptom_token(input_s: str, target_s: str) -> float:
    """Computes semantic overlap score between user-entered symptom and target database symptom."""
    i_norm = input_s.lower().replace('-', '_').replace(' ', '_').strip()
    t_norm = target_s.lower().replace('-', '_').replace(' ', '_').strip()
    if i_norm == t_norm or i_norm in t_norm or t_norm in i_norm:
        return 1.0
    i_tokens = set(i_norm.split('_')) - {'of', 'in', 'to', 'with', 'or', 'and', 'the'}
    t_tokens = set(t_norm.split('_')) - {'of', 'in', 'to', 'with', 'or', 'and', 'the'}
    if i_tokens & t_tokens:
        return 0.85
    for c_words in SYMPTOM_CLUSTERS.values():
        if any(w in i_norm for w in c_words) and any(w in t_norm for w in c_words):
            return 0.80
    return 0.0

def calculate_disease_posteriors(
    symptoms: List[str],
    qa_answers: Optional[Dict[str, Any]] = None,
    patient_context: Optional[Dict[str, Any]] = None,
    biomarkers: Optional[Dict[str, Any]] = None
) -> Dict[str, float]:
    """
    Computes normalized posterior probabilities across all diseases
    given observed symptoms, patient risk factors, and lab biomarkers.
    Dynamically separates hypotheses so different symptoms yield genuinely distinct distributions.
    """
    qa_answers = qa_answers or {}
    patient_context = patient_context or {}
    biomarkers = biomarkers or {}
    
    raw_scores = {}
    
    pre_existing_str = str(patient_context.get("pre_existing_conditions", "")).lower()
    age = patient_context.get("age", 35) or 35
    abnormal_biomarkers = " ".join(biomarkers.get("abnormal_flags", [])).lower()
    qa_str = " ".join([str(v) for v in qa_answers.values()]).lower()

    for d_name, d_info in DISEASES_DB.items():
        d_syms = d_info["symptoms"]
        
        # Calculate semantic match values across user symptoms
        m_vals = []
        for s in symptoms:
            best_match = max([match_symptom_token(s, ds) for ds in d_syms] + [0.0])
            m_vals.append(best_match)

        matched_count = sum(1 for v in m_vals if v >= 0.7)
        precision = sum(m_vals) / len(symptoms) if symptoms else 0.0
        recall = sum(m_vals) / len(d_syms) if d_syms else 0.0
        base_evidence = (0.6 * recall) + (0.4 * precision)

        # Baseline exponential scoring for distinct hypothesis discrimination
        if matched_count > 0:
            score = math.exp(3.2 * base_evidence)
        else:
            score = 0.05
        
        # Risk factor boosters
        if "cardiac" in d_name.lower() or "angina" in d_name.lower():
            if age >= 55:
                score *= 1.25
            if "hypertension" in pre_existing_str or "heart" in pre_existing_str or "diabetes" in pre_existing_str:
                score *= 1.35
            if "troponin" in abnormal_biomarkers or "ecg" in abnormal_biomarkers:
                score *= 2.5
            if "arm" in qa_str or "jaw" in qa_str or "exertion" in qa_str:
                score *= 1.6
        
        if "stroke" in d_name.lower():
            if "hypertension" in pre_existing_str or age >= 60:
                score *= 1.30
            if "droop" in qa_str or "slur" in qa_str or "thunderclap" in qa_str:
                score *= 2.0
                
        if "pneumonia" in d_name.lower():
            if "diabetes" in pre_existing_str or "copd" in pre_existing_str or "asthma" in pre_existing_str:
                score *= 1.25
            if "infiltrate" in abnormal_biomarkers or "wbc" in abnormal_biomarkers:
                score *= 2.2
            if "sputum" in qa_str or "phlegm" in qa_str or "cough" in qa_str:
                score *= 1.4

        if "dengue" in d_name.lower():
            if "platelet" in abnormal_biomarkers or "ns1" in abnormal_biomarkers:
                score *= 2.5
            if "rash" in qa_str or "petechiae" in qa_str:
                score *= 1.5

        if "cholecystitis" in d_name.lower():
            if "fatty" in qa_str or "right upper" in qa_str:
                score *= 1.8

        raw_scores[d_name] = max(score, 0.01)

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
