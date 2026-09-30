"""
Dynamic Next-Best-Question Engine using Information Gain.
Calculates expected Shannon entropy reduction IG(Q) = H(D) - E[H(D|Q)]
to determine the single optimal clinical question that maximally eliminates uncertainty.
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import DISEASES_DB
from .uncertainty_engine import calculate_disease_posteriors, compute_entropy_and_uncertainty

# Comprehensive clinical inquiry pool with hypothesis discriminators
QUESTION_BANK = [
    {
        "id": "q_pain_radiation",
        "question": "Does the discomfort radiate or spread anywhere else?",
        "options": [
            "Yes, spreads to left arm, neck, or lower jaw",
            "Spreads to upper back / between shoulder blades",
            "Radiates downward towards the groin or flank",
            "No radiation, stays strictly localized"
        ],
        "discriminates": ["Acute Coronary Syndrome / Angina (Cardiac Emergency)", "Acute Pyelonephritis / Complicated UTI"],
        "target_symptoms_boost": {
            "Yes, spreads to left arm, neck, or lower jaw": ["pain_radiating_to_arm_jaw"],
            "Radiates downward towards the groin or flank": ["flank_kidney_angle_pain"]
        }
    },
    {
        "id": "q_breathing_trigger",
        "question": "When does your shortness of breath or chest discomfort become worse?",
        "options": [
            "With physical exertion or climbing stairs, relieved by rest",
            "When lying completely flat on the bed (needs pillows to prop up)",
            "Constant difficulty breathing regardless of position or activity",
            "Worse only when coughing or taking a deep breath"
        ],
        "discriminates": ["Acute Coronary Syndrome / Angina (Cardiac Emergency)", "Bacterial Pneumonia / Lower Respiratory Infection"],
        "target_symptoms_boost": {
            "When lying completely flat on the bed (needs pillows to prop up)": ["orthopnea_lying_flat_breathless"]
        }
    },
    {
        "id": "q_fever_pattern",
        "question": "How does your body temperature behave during the day?",
        "options": [
            "High continuous spike with severe shivering chills and sweats",
            "Gradually climbs higher day by day (step-ladder fever)",
            "Mild low fever mainly towards evening",
            "No measured fever or completely normal temperature"
        ],
        "discriminates": ["Acute Dengue Infection with Warning Signs", "Typhoid Enteric Fever", "Bacterial Pneumonia / Lower Respiratory Infection"],
        "target_symptoms_boost": {
            "High continuous spike with severe shivering chills and sweats": ["chills"],
            "Gradually climbs higher day by day (step-ladder fever)": ["high_fever"]
        }
    },
    {
        "id": "q_headache_character",
        "question": "How quickly did the severe headache reach maximum intensity?",
        "options": [
            "Instantly within seconds, like a sudden thunderclap strike",
            "Gradually developed over several hours with throbbing on one side",
            "Dull constant heavy pressure across both temples and neck",
            "Associated with dizziness and room spinning"
        ],
        "discriminates": ["Acute Ischemic Stroke / Cerebrovascular Attack", "Migraine with Aura / Cluster Headache"],
        "target_symptoms_boost": {
            "Instantly within seconds, like a sudden thunderclap strike": ["sudden_thunderclap_headache"],
            "Associated with dizziness and room spinning": ["vertigo_room_spinning"]
        }
    },
    {
        "id": "q_abdominal_location",
        "question": "Where is your abdominal pain or distress primarily focused?",
        "options": [
            "Right upper side under the rib cage, worse after fatty foods",
            "Upper center burning behind the breastbone",
            "Diffuse cramping all over belly with watery loose stools",
            "Flank or lower back side near the kidney area"
        ],
        "discriminates": ["Acute Cholecystitis / Gallstone Pathology", "Gastroesophageal Reflux (GERD) & Peptic Ulcer", "Acute Gastroenteritis & Dehydration", "Acute Pyelonephritis / Complicated UTI"],
        "target_symptoms_boost": {
            "Right upper side under the rib cage, worse after fatty foods": ["right_upper_quadrant_pain"],
            "Upper center burning behind the breastbone": ["epigastric_burning_pain"],
            "Flank or lower back side near the kidney area": ["flank_kidney_angle_pain"]
        }
    },
    {
        "id": "q_bleeding_skin_spots",
        "question": "Have you noticed any unusual bleeding or skin discolorations?",
        "options": [
            "Tiny red or purple pin-point rash dots (petechiae) or bleeding gums",
            "Yellowing of the whites of your eyes or dark cola urine",
            "Itchy raised hives or welts that appear and fade",
            "None of the above"
        ],
        "discriminates": ["Acute Dengue Infection with Warning Signs", "Acute Cholecystitis / Gallstone Pathology", "Allergic Dermatitis & Urticaria"],
        "target_symptoms_boost": {
            "Tiny red or purple pin-point rash dots (petechiae) or bleeding gums": ["petechiae_purpura"],
            "Yellowing of the whites of your eyes or dark cola urine": ["yellowing_of_eyes_skin_jaundice", "dark_urine"],
            "Itchy raised hives or welts that appear and fade": ["hives_urticaria"]
        }
    },
    {
        "id": "q_neurological_focal",
        "question": "Have you noticed sudden weakness, facial change, or speech slurring?",
        "options": [
            "Yes, one side of face drooped or arm felt suddenly weak/numb",
            "Yes, words sounded garbled or slurred when speaking",
            "General tiredness/weakness all over body, no one-sided numbness",
            "No neurological weakness whatsoever"
        ],
        "discriminates": ["Acute Ischemic Stroke / Cerebrovascular Attack"],
        "target_symptoms_boost": {
            "Yes, one side of face drooped or arm felt suddenly weak/numb": ["facial_droop_weakness", "unilateral_limb_weakness"],
            "Yes, words sounded garbled or slurred when speaking": ["slurred_speech"]
        }
    }
]

def calculate_information_gain_for_question(
    q_data: Dict[str, Any],
    current_symptoms: List[str],
    current_entropy: float,
    qa_answers: Dict[str, Any],
    patient_context: Dict[str, Any]
) -> float:
    """
    Simulates posterior distributions across candidate answers to calculate expected Information Gain:
    IG(Q) = H_current - sum(P(answer_k) * H(D | answer_k))
    """
    options = q_data["options"]
    if not options:
        return 0.0

    p_option = 1.0 / len(options) # uniform prior over answer choices
    expected_conditional_entropy = 0.0

    for opt in options:
        # Simulate simulated symptoms boost
        simulated_symptoms = list(current_symptoms)
        boost_syms = q_data.get("target_symptoms_boost", {}).get(opt, [])
        for bs in boost_syms:
            if bs not in simulated_symptoms:
                simulated_symptoms.append(bs)

        # Compute simulated posterior
        sim_posteriors = calculate_disease_posteriors(
            symptoms=simulated_symptoms,
            qa_answers=qa_answers,
            patient_context=patient_context
        )
        sim_entropy = compute_entropy_and_uncertainty(sim_posteriors)["shannon_entropy"]
        expected_conditional_entropy += (p_option * sim_entropy)

    info_gain = max(current_entropy - expected_conditional_entropy, 0.0)
    return info_gain

def select_next_best_question(
    current_symptoms: List[str],
    answered_question_ids: List[str],
    qa_answers: Optional[Dict[str, Any]] = None,
    patient_context: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """
    Evaluates all unanswered clinical questions in the bank, computes their Information Gain,
    and returns the ranked best question with uncertainty reduction metrics.
    """
    qa_answers = qa_answers or {}
    patient_context = patient_context or {}
    answered_ids_set = set(answered_question_ids)

    # 1. Compute current posterior and entropy
    current_posteriors = calculate_disease_posteriors(
        symptoms=current_symptoms,
        qa_answers=qa_answers,
        patient_context=patient_context
    )
    entropy_info = compute_entropy_and_uncertainty(current_posteriors)
    current_entropy = entropy_info["shannon_entropy"]
    current_uncertainty = entropy_info["uncertainty_score"]

    # If uncertainty is already low (< 20%), no further questions are mandatory
    if current_uncertainty <= 20.0:
        return None

    # 2. Evaluate Information Gain across eligible questions
    candidates = []
    for q in QUESTION_BANK:
        if q["id"] in answered_ids_set:
            continue
            
        ig = calculate_information_gain_for_question(
            q_data=q,
            current_symptoms=current_symptoms,
            current_entropy=current_entropy,
            qa_answers=qa_answers,
            patient_context=patient_context
        )
        
        # Relevance multiplier: if top competing diseases overlap with q["discriminates"]
        top_candidates = [c["disease"] for c in entropy_info["candidate_distribution"][:3]]
        overlap_count = sum(1 for d in q["discriminates"] if d in top_candidates)
        relevance_score = ig * (1.0 + (overlap_count * 0.8))

        candidates.append({
            "question_data": q,
            "information_gain": round(ig, 3),
            "relevance_score": round(relevance_score, 3),
            "expected_uncertainty_reduction_pct": round(min((ig / max(current_entropy, 0.1)) * 100, 75.0), 1),
            "target_hypotheses": q["discriminates"]
        })

    if not candidates:
        return None

    # Sort descending by relevance & information gain
    candidates.sort(key=lambda x: (x["relevance_score"], x["information_gain"]), reverse=True)
    best = candidates[0]

    q_data = best["question_data"]
    return {
        "question_id": q_data["id"],
        "question": q_data["question"],
        "options": q_data["options"],
        "information_gain": best["information_gain"],
        "expected_entropy_reduction": best["expected_uncertainty_reduction_pct"],
        "rationale": f"Maximizes Information Gain ({best['information_gain']} bits) to discriminate between {', '.join(best['target_hypotheses'][:2])}.",
        "current_uncertainty_score": current_uncertainty
    }
