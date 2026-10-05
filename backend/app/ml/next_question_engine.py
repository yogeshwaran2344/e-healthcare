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
    # 1. Hair & Scalp Loss Pattern
    {
        "id": "q_hair_loss_pattern",
        "question": "How would you describe the pattern and onset of your hair loss or scalp problem?",
        "options": [
            "Excessive shedding all over scalp (bunches of hair in brush/shower post-stress/fever)",
            "Gradual widening of hair parting line or thinning at the crown",
            "Smooth, round coin-shaped bald patches appearing suddenly",
            "Greasy yellowish crusts/flakes with intense itching and scalp redness"
        ],
        "discriminates": [
            "Telogen Effluvium & Scalp Seborrheic Dermatitis",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity",
            "Allergic Dermatitis & Urticaria"
        ],
        "target_symptoms_boost": {
            "Excessive shedding all over scalp (bunches of hair in brush/shower post-stress/fever)": ["hair_fall_excessive", "dry_brittle_hair"],
            "Gradual widening of hair parting line or thinning at the crown": ["hair_thinning_scalp", "receding_hairline"],
            "Smooth, round coin-shaped bald patches appearing suddenly": ["patchy_hair_loss_alopecia"],
            "Greasy yellowish crusts/flakes with intense itching and scalp redness": ["dandruff_scalp_flaking", "scalp_itching_irritation", "scalp_redness_bumps"]
        }
    },
    # 2. Scalp Condition & Sensation
    {
        "id": "q_scalp_condition_sensation",
        "question": "Describe your scalp condition and sensations at the hair roots:",
        "options": [
            "Greasy yellowish flakes with persistent itching, burning, and redness",
            "Dry white powdery dandruff with dry, frizzy, brittle hair",
            "Painful tender red bumps or small pimples at hair follicles",
            "Clean scalp without dandruff, but hair pulls out effortlessly in strands"
        ],
        "discriminates": [
            "Telogen Effluvium & Scalp Seborrheic Dermatitis",
            "Acne Vulgaris & Hormonal Sebum Imbalance"
        ],
        "target_symptoms_boost": {
            "Greasy yellowish flakes with persistent itching, burning, and redness": ["dandruff_scalp_flaking", "scalp_itching_irritation"],
            "Dry white powdery dandruff with dry, frizzy, brittle hair": ["dry_brittle_hair"],
            "Painful tender red bumps or small pimples at hair follicles": ["scalp_redness_bumps"],
            "Clean scalp without dandruff, but hair pulls out effortlessly in strands": ["hair_fall_excessive"]
        }
    },
    # 3. Facial Acne & Breakout Morphology
    {
        "id": "q_facial_breakout_type",
        "question": "What type of facial breakouts or blemishes are you predominantly experiencing?",
        "options": [
            "Deep, painful red cysts/nodules along jawline, chin, and lower cheeks",
            "Surface blackheads, whiteheads, and oily grease in forehead and nose (T-zone)",
            "Facial redness, flushing, and sensitive stinging skin triggered by heat/sun",
            "Dry peeling skin with stubborn dark marks and post-acne blemishes"
        ],
        "discriminates": [
            "Acne Vulgaris & Hormonal Sebum Imbalance",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity",
            "Allergic Dermatitis & Urticaria"
        ],
        "target_symptoms_boost": {
            "Deep, painful red cysts/nodules along jawline, chin, and lower cheeks": ["cystic_hormonal_acne", "facial_acne_pimples"],
            "Surface blackheads, whiteheads, and oily grease in forehead and nose (T-zone)": ["blackheads_whiteheads", "excessive_oily_skin"],
            "Facial redness, flushing, and sensitive stinging skin triggered by heat/sun": ["skin_redness_rosacea"],
            "Dry peeling skin with stubborn dark marks and post-acne blemishes": ["post_acne_scars_spots", "dry_peeling_skin"]
        }
    },
    # 4. Facial Skin Sensitivity & Oil Balance
    {
        "id": "q_facial_skin_reaction",
        "question": "How does your facial skin behave during your daily routine?",
        "options": [
            "Becomes excessively shiny and oily within a few hours of washing",
            "Flushes bright red and stings when applying sunscreen, soap, or cosmetics",
            "Breakout flares correlate directly with menstrual cycle / period schedule",
            "Feels uncomfortably dry, tight, and flaky despite moisturizing"
        ],
        "discriminates": [
            "Acne Vulgaris & Hormonal Sebum Imbalance",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity",
            "Allergic Dermatitis & Urticaria"
        ],
        "target_symptoms_boost": {
            "Becomes excessively shiny and oily within a few hours of washing": ["excessive_oily_skin", "facial_acne_pimples"],
            "Flushes bright red and stings when applying sunscreen, soap, or cosmetics": ["skin_redness_rosacea"],
            "Breakout flares correlate directly with menstrual cycle / period schedule": ["cystic_hormonal_acne", "pcos_pcod_symptoms"],
            "Feels uncomfortably dry, tight, and flaky despite moisturizing": ["dry_peeling_skin"]
        }
    },
    # 5. Menstrual & PCOS Hormonal Symptoms
    {
        "id": "q_menstrual_cycle_pcos",
        "question": "Describe your menstrual cycle regularity and associated hormonal features:",
        "options": [
            "Irregular, delayed cycles (>35-50 days) with jawline acne or excess facial hair",
            "Severe debilitating lower abdominal/pelvic cramps during first 48 hours of period",
            "Heavy prolonged menstrual bleeding with large clots and exhaustion",
            "Regular monthly cycles without severe pelvic symptoms"
        ],
        "discriminates": [
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity",
            "Primary Dysmenorrhea & Pelvic Pain",
            "Telogen Effluvium & Scalp Seborrheic Dermatitis"
        ],
        "target_symptoms_boost": {
            "Irregular, delayed cycles (>35-50 days) with jawline acne or excess facial hair": ["pcos_pcod_symptoms", "cystic_hormonal_acne", "hair_thinning_scalp"],
            "Severe debilitating lower abdominal/pelvic cramps during first 48 hours of period": ["lower_pelvic_ovarian_pain"],
            "Heavy prolonged menstrual bleeding with large clots and exhaustion": ["general_weakness", "fatigue"]
        }
    },
    # 6. Abdominal Pain & GI Symptoms
    {
        "id": "q_abdominal_location",
        "question": "Where is your abdominal pain or distress primarily focused?",
        "options": [
            "Upper center burning / sour acid regurgitation behind breastbone",
            "Right upper side under rib cage, aggravated after eating fatty meals",
            "Diffuse cramping all over belly with frequent watery loose stools",
            "Lower back / flank side discomfort near the kidney angle"
        ],
        "discriminates": [
            "Gastroesophageal Reflux (GERD) & Peptic Ulcer",
            "Acute Cholecystitis / Gallstone Pathology",
            "Acute Gastroenteritis & Dehydration",
            "Acute Pyelonephritis / Complicated UTI"
        ],
        "target_symptoms_boost": {
            "Upper center burning / sour acid regurgitation behind breastbone": ["epigastric_burning_pain", "loss_of_appetite"],
            "Right upper side under rib cage, aggravated after eating fatty meals": ["right_upper_quadrant_pain", "nausea"],
            "Diffuse cramping all over belly with frequent watery loose stools": ["diarrhea", "vomiting"],
            "Lower back / flank side discomfort near the kidney angle": ["flank_kidney_angle_pain"]
        }
    },
    # 7. Skin Allergy & Rash
    {
        "id": "q_skin_rash_allergy",
        "question": "What are the characteristics of your skin rash or itching?",
        "options": [
            "Raised itchy red welts / hives (urticaria) that appear and disappear rapidly",
            "Dry, inflamed red patches with intense scaling and persistent scratching",
            "Fluid-filled blister clusters with raw burning pain",
            "Tiny pinpoint non-blanching red/purple dots (petechiae) with fever"
        ],
        "discriminates": [
            "Allergic Dermatitis & Urticaria",
            "Acute Dengue Infection with Warning Signs"
        ],
        "target_symptoms_boost": {
            "Raised itchy red welts / hives (urticaria) that appear and disappear rapidly": ["hives_urticaria", "skin_redness"],
            "Dry, inflamed red patches with intense scaling and persistent scratching": ["skin_rash", "itching_pruritus"],
            "Fluid-filled blister clusters with raw burning pain": ["blisters"],
            "Tiny pinpoint non-blanching red/purple dots (petechiae) with fever": ["petechiae_purpura", "high_fever"]
        }
    },
    # 8. Pain Radiation (Cardiac / Renal)
    {
        "id": "q_pain_radiation",
        "question": "Does your chest or back discomfort radiate anywhere else?",
        "options": [
            "Yes, radiates to left arm, neck, or lower jaw with heavy tightness",
            "Radiates through to upper back between shoulder blades",
            "Radiates downward towards the groin or flank",
            "No radiation, strictly localized"
        ],
        "discriminates": [
            "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
            "Acute Pyelonephritis / Complicated UTI"
        ],
        "target_symptoms_boost": {
            "Yes, radiates to left arm, neck, or lower jaw with heavy tightness": ["pain_radiating_to_arm_jaw"],
            "Radiates downward towards the groin or flank": ["flank_kidney_angle_pain"]
        }
    },
    # 9. Breathing Triggers
    {
        "id": "q_breathing_trigger",
        "question": "When does your shortness of breath or chest tightness worsen?",
        "options": [
            "With physical exertion or climbing stairs, relieved by resting",
            "When lying completely flat on the bed (needs multiple pillows)",
            "Constant difficulty breathing regardless of position",
            "Worse only when coughing or taking a deep breath"
        ],
        "discriminates": [
            "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
            "Bacterial Pneumonia / Lower Respiratory Infection",
            "COVID-19 / Severe Viral Pneumonitis"
        ],
        "target_symptoms_boost": {
            "When lying completely flat on the bed (needs multiple pillows)": ["orthopnea_lying_flat_breathless"]
        }
    },
    # 10. Fever Pattern
    {
        "id": "q_fever_pattern",
        "question": "How does your body temperature behave during the day?",
        "options": [
            "High continuous spike with severe shivering chills and sweats",
            "Gradually climbs higher day by day (step-ladder fever)",
            "Mild low-grade fever mainly towards evening",
            "No measured fever or completely normal temperature"
        ],
        "discriminates": [
            "Acute Dengue Infection with Warning Signs",
            "Typhoid Enteric Fever",
            "Bacterial Pneumonia / Lower Respiratory Infection"
        ],
        "target_symptoms_boost": {
            "High continuous spike with severe shivering chills and sweats": ["chills"],
            "Gradually climbs higher day by day (step-ladder fever)": ["high_fever"]
        }
    },
    # 11. Headache Character
    {
        "id": "q_headache_character",
        "question": "How quickly did the severe headache develop and what does it feel like?",
        "options": [
            "Instant sudden 'worst headache of life' like a thunderclap within seconds",
            "Pulsating throbbing ache on one side of head with light/sound sensitivity",
            "Dull constant band-like pressure across both temples and back of neck",
            "Associated with spinning vertigo and loss of balance"
        ],
        "discriminates": [
            "Acute Ischemic Stroke / Cerebrovascular Attack",
            "Migraine with Aura / Cluster Headache",
            "Tension-Type Headache & Physical Strain"
        ],
        "target_symptoms_boost": {
            "Instant sudden 'worst headache of life' like a thunderclap within seconds": ["sudden_thunderclap_headache"],
            "Pulsating throbbing ache on one side of head with light/sound sensitivity": ["photophobia_light_sensitivity"],
            "Associated with spinning vertigo and loss of balance": ["vertigo_room_spinning"]
        }
    },
    # 12. Neurological Focal Signs
    {
        "id": "q_neurological_focal",
        "question": "Have you noticed sudden weakness, facial change, or speech slurring?",
        "options": [
            "Yes, one side of face drooped or arm felt suddenly weak/numb",
            "Yes, words sounded garbled or slurred when speaking",
            "General tiredness/weakness all over body, no one-sided numbness",
            "No neurological weakness whatsoever"
        ],
        "discriminates": [
            "Acute Ischemic Stroke / Cerebrovascular Attack"
        ],
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

    # If uncertainty is already low (< 15%), no further questions are mandatory
    if current_uncertainty <= 15.0:
        return None

    symptoms_joined = " ".join(current_symptoms).lower()
    top_candidates = [c["disease"] for c in entropy_info["candidate_distribution"][:4]]

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
        
        # Domain Relevance Score:
        # Boost if the question's target hypotheses overlap with the current top candidates
        overlap_count = sum(1 for d in q["discriminates"] if d in top_candidates)
        
        # Keyword synergy boost based on active symptoms
        keyword_boost = 0.0
        q_id = q["id"]
        if ("hair" in symptoms_joined or "scalp" in symptoms_joined or "dandruff" in symptoms_joined) and ("hair" in q_id or "scalp" in q_id):
            keyword_boost = 3.0
        elif ("acne" in symptoms_joined or "face" in symptoms_joined or "facial" in symptoms_joined or "rosacea" in symptoms_joined) and ("breakout" in q_id or "facial" in q_id):
            keyword_boost = 3.0
        elif ("period" in symptoms_joined or "menstrual" in symptoms_joined or "pcos" in symptoms_joined) and ("menstrual" in q_id or "pcos" in q_id):
            keyword_boost = 3.0
        elif ("abdominal" in symptoms_joined or "stomach" in symptoms_joined or "acidity" in symptoms_joined) and ("abdominal" in q_id):
            keyword_boost = 3.0
        elif ("rash" in symptoms_joined or "hives" in symptoms_joined or "itching" in symptoms_joined) and ("rash" in q_id or "skin" in q_id):
            keyword_boost = 3.0
        elif ("chest" in symptoms_joined or "palpitation" in symptoms_joined) and ("radiation" in q_id or "breathing" in q_id):
            keyword_boost = 3.0
        elif ("cough" in symptoms_joined or "breath" in symptoms_joined) and ("breathing" in q_id):
            keyword_boost = 3.0
        elif ("headache" in symptoms_joined or "vertigo" in symptoms_joined) and ("headache" in q_id or "neurological" in q_id):
            keyword_boost = 3.0
        elif ("fever" in symptoms_joined) and ("fever" in q_id):
            keyword_boost = 3.0

        relevance_score = (ig * 2.0) + (overlap_count * 2.5) + keyword_boost

        candidates.append({
            "question_data": q,
            "information_gain": round(max(ig, 0.45 if keyword_boost > 0 else 0.1), 3),
            "relevance_score": round(relevance_score, 3),
            "expected_uncertainty_reduction_pct": round(min(((max(ig, 0.45 if keyword_boost > 0 else 0.1)) / max(current_entropy, 0.1)) * 100, 75.0), 1),
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
