"""
Adaptive Multi-Stage Question Engine, Context-Aware Bayesian Predictor,
3-Tier Risk Triage & Explainable AI (XAI).
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import ALL_SYMPTOMS, DISEASES_DB
from .uncertainty_engine import calculate_disease_posteriors, compute_entropy_and_uncertainty
from .explainable_map_engine import generate_explainable_decision_map
from .test_optimization_engine import optimize_minimum_diagnostic_test_set

# Symptom-specific targeted clinical follow-up questions
SYMPTOM_SPECIFIC_QUESTIONS = {
    "fever": {
        "question": "What is your highest measured body temperature, and do you have chills or shivering?",
        "options": ["Mild fever (around 99-100°F), no chills", "Moderate (101-102°F) with shivering", "High spike (>102.5°F) with intense chills", "Haven't measured thermometer yet"]
    },
    "cough": {
        "question": "How would you describe your cough?",
        "options": ["Dry tickly cough, no phlegm", "Wet productive cough with clear/white phlegm", "Deep chest cough with yellow or green phlegm", "Barking cough with shortness of breath"]
    },
    "chest": {
        "question": "Describe the chest discomfort:",
        "options": ["Heavy pressure / squeezing in center of chest", "Sharp pain that worsens when breathing in deeply", "Burning sensation behind breastbone after meals", "Mild muscle tenderness on movement"]
    },
    "headache": {
        "question": "Characterize your headache:",
        "options": ["Throbbing on one side with light sensitivity", "Dull tight band around the entire head", "Sudden 'thunderclap' severe headache with stiff neck", "Forehead and sinus heaviness with runny nose"]
    },
    "abdominal": {
        "question": "Where is the abdominal discomfort most intense?",
        "options": ["Upper center (stomach / burning acidity)", "Right upper quadrant near ribs", "Lower abdomen with cramps and diarrhea", "Generalized discomfort with nausea"]
    },
    "breathlessness": {
        "question": "When does shortness of breath occur?",
        "options": ["Only during exertion / climbing stairs", "Even when resting or lying flat in bed", "Sudden acute onset with wheezing", "Accompanied by chest tightness and palpitations"]
    },
    "rash": {
        "question": "Describe the skin eruption:",
        "options": ["Itchy red patches / dry scaling", "Raised hives that appeared suddenly", "Blisters or pustules with burning sensation", "Tiny red/purple spots (petechiae)"]
    }
}

def generate_adaptive_questions(selected_symptoms: List[str], patient_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Dynamically generates 3-5 clinical follow-up questions based on the selected symptoms
    and individual patient context (age, history).
    """
    questions = []
    
    # 1. Onset & Duration (Standard Clinical inquiry)
    questions.append({
        "id": "duration_days",
        "question": "How many days have you been experiencing these primary symptoms?",
        "type": "select",
        "options": ["1-2 days (acute onset)", "3-5 days (persistent)", "1-2 weeks", "More than 2 weeks (chronic)"]
    })

    # 2. Pain / Discomfort Intensity (Numeric Rating Scale 1-10)
    questions.append({
        "id": "severity_scale",
        "question": "On a scale from 1 (mild) to 10 (unbearable), how severe is your overall discomfort?",
        "type": "select",
        "options": ["1 - 3 (Mild, able to do normal activities)", "4 - 6 (Moderate, interfering with work/sleep)", "7 - 8 (Severe, causing significant distress)", "9 - 10 (Extreme, unbearable agony)"]
    })

    # 3. Targeted symptom-specific questions
    symptoms_joined = " ".join(selected_symptoms).lower()
    matched_keys = set()
    for key, q_data in SYMPTOM_SPECIFIC_QUESTIONS.items():
        if key in symptoms_joined and key not in matched_keys:
            questions.append({
                "id": f"specific_{key}",
                "question": q_data["question"],
                "type": "select",
                "options": q_data["options"]
            })
            matched_keys.add(key)
            if len(questions) >= 4:
                break

    # 4. Medication & Pre-existing Context
    questions.append({
        "id": "prior_meds_taken",
        "question": "Have you taken any home remedies or over-the-counter medications for this?",
        "type": "select",
        "options": ["None yet", "Paracetamol / Acetaminophen (fever/pain)", "Antacids / Digestion tablets", "Painkillers (Ibuprofen / Aspirin)", "Antibiotics or prescribed drugs"]
    })

    return questions

def evaluate_risk_triage(
    symptoms: List[str],
    top_disease: str,
    confidence: float,
    qa_answers: Dict[str, Any],
    patient_context: Dict[str, Any],
    biomarkers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Determines 3-Tier Clinical Triage Level:
    - RED: Emergency Care (immediate ER / emergency hospital care)
    - YELLOW: Doctor Consultation (scheduled teleconsultation or clinic review)
    - GREEN: Self-Care / Home Monitoring
    """
    reasons = []
    is_emergency = False

    symptoms_lower = [s.lower() for s in symptoms]
    severity_ans = qa_answers.get("severity_scale", "")
    duration_ans = qa_answers.get("duration_days", "")

    # Red Flag Rules
    red_flag_symptoms = [
        "sharp_chest_pain", "breathlessness_shortness_of_breath", "stiff_neck"
    ]
    for rf in red_flag_symptoms:
        if rf in symptoms_lower:
            if rf == "sharp_chest_pain":
                reasons.append("Reported acute sharp chest pain (potential cardiac/pulmonary compromise).")
                is_emergency = True
            elif rf == "breathlessness_shortness_of_breath" and ("resting" in str(qa_answers) or "severe" in severity_ans.lower()):
                reasons.append("Severe respiratory distress / dyspnea reported.")
                is_emergency = True
            elif rf == "stiff_neck" and any("fever" in s for s in symptoms_lower):
                reasons.append("Meningeal irritation sign: stiff neck accompanied by fever.")
                is_emergency = True

    if "9 - 10" in severity_ans:
        reasons.append("Extreme pain rating (9-10/10) indicates acute clinical distress.")
        is_emergency = True

    # Biomarker red flags
    if biomarkers:
        abnormals = biomarkers.get("abnormal_flags", [])
        for ab in abnormals:
            if "Critical" in ab or "Danger" in ab or "Very Low Platelets" in ab:
                reasons.append(f"Critical lab alert: {ab}")
                is_emergency = True

    # Patient Context Modifiers (Elderly or pre-existing cardiac/pulmonary)
    age = patient_context.get("age", 30)
    pre_existing = str(patient_context.get("pre_existing_conditions", "")).lower()
    symptoms_joined = " ".join(symptoms_lower)
    if age and age >= 65 and ("fever" in symptoms_joined):
        reasons.append(f"Geriatric patient (Age {age}) with systemic symptoms requires heightened clinical surveillance.")

    if is_emergency:
        triage_level = "Emergency Care"
        badge_color = "danger"
        action_text = "EMERGENCY: Proceed to the nearest Hospital Emergency Room or call emergency medical services immediately."
    elif (
        len(symptoms) >= 3 or
        "More than 2 weeks" in duration_ans or
        "7 - 8" in severity_ans or
        confidence >= 75.0 or
        bool(biomarkers.get("abnormal_flags"))
    ):
        triage_level = "Doctor Consultation"
        badge_color = "warning"
        action_text = "Consultation Recommended: Schedule a virtual or in-person consultation with a physician for definitive diagnosis and prescription."
    else:
        triage_level = "Self-Care"
        badge_color = "success"
        action_text = "Self-Care & Observation: Symptoms suggest a mild self-limiting condition. Hydrate, rest, and monitor for 48 hours."

    return {
        "triage_level": triage_level,
        "badge_color": badge_color,
        "action_text": action_text,
        "triage_reasons": reasons
    }

def compute_explainable_diagnosis(
    symptoms: List[str],
    qa_answers: Dict[str, Any],
    patient_context: Dict[str, Any],
    biomarkers: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Context-aware Bayesian condition classifier with full Explainable AI (XAI) rationale.
    Integrates symptom vector + lab biomarkers + pre-existing conditions.
    """
    input_set = set(symptoms)
    all_symptom_set = set(ALL_SYMPTOMS)
    valid_symptoms = [s for s in symptoms if s in all_symptom_set]
    
    disease_scores = []
    
    # Biomarker hints
    biomarker_keywords = " ".join(biomarkers.get("abnormal_flags", [])).lower()
    pre_existing_str = str(patient_context.get("pre_existing_conditions", "")).lower()

    for disease_name, info in DISEASES_DB.items():
        disease_symptoms = set(info["symptoms"])
        matching_symptoms = list(input_set & disease_symptoms)
        match_count = len(matching_symptoms)
        total_disease_sym = len(disease_symptoms)
        
        # Base Jaccard + Overlap
        overlap_score = match_count / total_disease_sym if total_disease_sym > 0 else 0
        input_overlap = match_count / len(input_set) if len(input_set) > 0 else 0
        
        score = (overlap_score * 0.5) + (input_overlap * 0.5)

        xai_factors = []
        if matching_symptoms:
            readable_matched = [s.replace('_', ' ') for s in matching_symptoms]
            xai_factors.append(f"Matched {match_count} core symptoms: {', '.join(readable_matched)}.")

        # Biomarker synergy boost
        if "platelet" in biomarker_keywords and "dengue" in disease_name.lower():
            score += 0.40
            xai_factors.append("Uploaded lab report confirms thrombocytopenia (low platelets), strongly elevating Dengue suspicion.")
        elif "wbc" in biomarker_keywords and ("pneumonia" in disease_name.lower() or "typhoid" in disease_name.lower()):
            score += 0.30
            xai_factors.append("Elevated white blood cell count (leukocytosis) in uploaded report indicates active bacterial infection.")
        elif "bilirubin" in biomarker_keywords and "jaundice" in disease_name.lower():
            score += 0.45
            xai_factors.append("Elevated total serum bilirubin in lab panel directly supports hepatic/jaundice diagnosis.")
        elif "infiltrate" in biomarker_keywords or "opacity" in biomarker_keywords and "pneumonia" in disease_name.lower():
            score += 0.45
            xai_factors.append("Radiology/Chest scan findings show lung opacity consistent with pneumonia consolidation.")

        # Patient history synergy boost
        if "diabetes" in pre_existing_str:
            if "pneumonia" in disease_name.lower() or "covid" in disease_name.lower():
                score += 0.10
                xai_factors.append(f"Pre-existing Diabetes increases vulnerability to lower respiratory tract infections.")
        if "hypertension" in pre_existing_str or "heart" in pre_existing_str:
            if "angina" in disease_name.lower() or "cardiovascular" in disease_name.lower():
                score += 0.25
                xai_factors.append("Documented cardiovascular medical history compounds risk of acute coronary syndrome.")

        disease_scores.append({
            "disease": disease_name,
            "score": score,
            "info": info,
            "xai_factors": xai_factors
        })

    # Sort descending
    disease_scores.sort(key=lambda x: x["score"], reverse=True)
    top = disease_scores[0]
    
    # Calculate calibrated confidence
    raw_confidence = top["score"] * 100
    confidence = min(max(raw_confidence, 35.0), 98.0)

    alternatives = []
    for alt in disease_scores[1:4]:
        if alt["score"] > 0.15:
            alternatives.append({
                "disease": alt["disease"],
                "confidence_percentage": round(min(alt["score"] * 85, 90.0), 1),
                "specialist": alt["info"].get("specialist", "General Physician"),
                "reason": alt["xai_factors"][0] if alt["xai_factors"] else "Partial symptom overlap"
            })

    triage = evaluate_risk_triage(
        symptoms=symptoms,
        top_disease=top["disease"],
        confidence=confidence,
        qa_answers=qa_answers,
        patient_context=patient_context,
        biomarkers=biomarkers
    )

    # Closed-Loop Adaptive Intelligence Additions
    posteriors = calculate_disease_posteriors(symptoms, qa_answers, patient_context, biomarkers)
    entropy_uncertainty = compute_entropy_and_uncertainty(posteriors)
    
    candidate_list = [{"disease": d, "probability": p} for d, p in posteriors.items()]
    candidate_list.sort(key=lambda x: x["probability"], reverse=True)

    min_test_set = optimize_minimum_diagnostic_test_set(
        top_disease=top["disease"],
        top_candidates=candidate_list,
        current_uncertainty=entropy_uncertainty["uncertainty_score"],
        symptoms=symptoms,
        triage_level=triage["triage_level"]
    )

    decision_map = generate_explainable_decision_map(
        target_disease=top["disease"],
        symptoms=symptoms,
        qa_answers=qa_answers,
        patient_context=patient_context,
        biomarkers=biomarkers,
        confidence_percentage=confidence
    )

    return {
        "top_disease": top["disease"],
        "confidence_percentage": round(confidence, 1),
        "severity": top["info"].get("severity", "Moderate"),
        "specialist_recommended": top["info"].get("specialist", "General Physician"),
        "medical_advice": top["info"].get("advice", ""),
        "recommended_diagnostic_tests": top["info"].get("recommended_tests", ["Complete Blood Count (CBC)"]),
        "triage": triage,
        "xai_reasoning": top["xai_factors"],
        "other_possibilities": alternatives,
        # Closed-loop enhancements
        "entropy_uncertainty": entropy_uncertainty,
        "explainable_decision_map": decision_map,
        "minimum_diagnostic_test_set": min_test_set
    }

