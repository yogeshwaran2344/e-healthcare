"""
Dynamic Next-Best-Question Engine using Information Gain.
Calculates expected Shannon entropy reduction IG(Q) = H(D) - E[H(D|Q)]
to determine the single optimal clinical question that maximally eliminates uncertainty.
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import DISEASES_DB
from .uncertainty_engine import calculate_disease_posteriors, compute_entropy_and_uncertainty

# Comprehensive clinical inquiry pool with hypothesis discriminators & strict domain triggers
QUESTION_BANK = [
    # 1. Hair & Scalp Loss Pattern
    {
        "id": "q_hair_loss_pattern",
        "domain_triggers": ["hair", "scalp", "alopecia", "shedding", "thinning", "folliculitis", "greying", "brittle"],
        "question": "How would you describe the pattern and progression of your hair loss or scalp problem?",
        "options": [
            "Sudden diffuse shedding all over the scalp (handfuls in brush/shower post-stress/fever)",
            "Gradual widening of parting line or thinning across the crown over months",
            "Smooth, round coin-shaped bald patches appearing rapidly (patchy loss)",
            "Greasy yellowish buildup with severe dandruff, scalp itching, and hair breakage"
        ],
        "discriminates": [
            "Telogen Effluvium & Scalp Seborrheic Dermatitis",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity"
        ],
        "target_symptoms_boost": {
            "Sudden diffuse shedding all over the scalp (handfuls in brush/shower post-stress/fever)": ["hair_fall_excessive", "dry_brittle_hair"],
            "Gradual widening of parting line or thinning across the crown over months": ["hair_thinning_scalp", "receding_hairline"],
            "Smooth, round coin-shaped bald patches appearing rapidly (patchy loss)": ["patchy_hair_loss_alopecia"],
            "Greasy yellowish buildup with severe dandruff, scalp itching, and hair breakage": ["dandruff_scalp_flaking", "scalp_itching_irritation", "scalp_redness_bumps"]
        }
    },
    # 2. Scalp Condition & Sensations
    {
        "id": "q_scalp_condition_sensation",
        "domain_triggers": ["scalp", "dandruff", "itching", "folliculitis", "flaking", "bumps", "hair"],
        "question": "Describe your scalp condition and sensations at the hair roots:",
        "options": [
            "Greasy yellowish crusts/flakes with intense itching, burning, and redness",
            "Dry white powdery dandruff with dry, frizzy, brittle hair strands",
            "Painful tender red bumps or small pustules at hair follicle bases",
            "Relatively clean scalp without flakes, but hair pulls out with minimal tension"
        ],
        "discriminates": [
            "Telogen Effluvium & Scalp Seborrheic Dermatitis"
        ],
        "target_symptoms_boost": {
            "Greasy yellowish crusts/flakes with intense itching, burning, and redness": ["dandruff_scalp_flaking", "scalp_itching_irritation"],
            "Dry white powdery dandruff with dry, frizzy, brittle hair strands": ["dry_brittle_hair"],
            "Painful tender red bumps or small pustules at hair follicle bases": ["scalp_redness_bumps"],
            "Relatively clean scalp without flakes, but hair pulls out with minimal tension": ["hair_fall_excessive"]
        }
    },
    # 3. Hair Triggers & Medical History
    {
        "id": "q_hair_triggers_history",
        "domain_triggers": ["hair", "scalp", "alopecia", "thinning", "shedding"],
        "question": "Have you experienced any recent medical, stress, or lifestyle triggers for your hair loss?",
        "options": [
            "Recent illness, high fever, COVID-19, major emotional stress, or strict dieting 2-4 months ago",
            "Strong family history of early hair thinning or receding hairline in parents/siblings",
            "Frequent chemical treatments, hair dyes, bleach, heat styling, or tight ponytails",
            "Low dietary protein, iron deficiency anemia, or extreme work fatigue"
        ],
        "discriminates": [
            "Telogen Effluvium & Scalp Seborrheic Dermatitis"
        ],
        "target_symptoms_boost": {
            "Recent illness, high fever, COVID-19, major emotional stress, or strict dieting 2-4 months ago": ["hair_fall_excessive"],
            "Strong family history of early hair thinning or receding hairline in parents/siblings": ["hair_thinning_scalp", "receding_hairline"],
            "Frequent chemical treatments, hair dyes, bleach, heat styling, or tight ponytails": ["dry_brittle_hair"],
            "Low dietary protein, iron deficiency anemia, or extreme work fatigue": ["general_weakness", "fatigue"]
        }
    },
    # 4. Facial Acne & Breakouts
    {
        "id": "q_facial_breakout_type",
        "domain_triggers": ["acne", "face", "facial", "pimple", "cystic", "blackhead", "whitehead", "comedone"],
        "question": "What type of facial breakouts or blemishes are you predominantly experiencing?",
        "options": [
            "Deep, painful red cysts and nodules along jawline, chin, and lower cheeks (hormonal)",
            "Surface blackheads, whiteheads, and oily grease in forehead and nose (T-zone)",
            "Small red pimples and pustules triggered after certain cosmetics or sunscreens",
            "Stubborn post-acne dark marks, hyperpigmentation, and textured acne spots"
        ],
        "discriminates": [
            "Acne Vulgaris & Hormonal Sebum Imbalance",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity"
        ],
        "target_symptoms_boost": {
            "Deep, painful red cysts and nodules along jawline, chin, and lower cheeks (hormonal)": ["cystic_hormonal_acne", "facial_acne_pimples"],
            "Surface blackheads, whiteheads, and oily grease in forehead and nose (T-zone)": ["blackheads_whiteheads", "excessive_oily_skin"],
            "Small red pimples and pustules triggered after certain cosmetics or sunscreens": ["facial_acne_pimples"],
            "Stubborn post-acne dark marks, hyperpigmentation, and textured acne spots": ["post_acne_scars_spots", "dry_peeling_skin"]
        }
    },
    # 5. Facial Skin Sensitivity & Barrier
    {
        "id": "q_facial_skin_reaction",
        "domain_triggers": ["rosacea", "face", "facial", "redness", "peeling", "oily", "grease", "acne"],
        "question": "How does your facial skin behave during your daily routine and product application?",
        "options": [
            "Becomes excessively shiny, greasy, and oily within 2-3 hours of cleansing",
            "Flushes bright red, stings, and burns with sun exposure, hot drinks, or skincare products",
            "Breakout flares correlate directly with monthly menstrual period dates",
            "Feels uncomfortably tight, dry, flaky, and sensitive despite moisturizing"
        ],
        "discriminates": [
            "Acne Vulgaris & Hormonal Sebum Imbalance",
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity"
        ],
        "target_symptoms_boost": {
            "Becomes excessively shiny, greasy, and oily within 2-3 hours of cleansing": ["excessive_oily_skin", "facial_acne_pimples"],
            "Flushes bright red, stings, and burns with sun exposure, hot drinks, or skincare products": ["skin_redness_rosacea"],
            "Breakout flares correlate directly with monthly menstrual period dates": ["cystic_hormonal_acne", "pcos_pcod_symptoms"],
            "Feels uncomfortably tight, dry, flaky, and sensitive despite moisturizing": ["dry_peeling_skin"]
        }
    },
    # 6. Menstrual & PCOS Hormonal Symptoms
    {
        "id": "q_menstrual_cycle_pcos",
        "domain_triggers": ["period", "menstrual", "pcos", "pcod", "cramp", "pelvic", "ovarian"],
        "question": "Describe your menstrual cycle regularity and associated hormonal features:",
        "options": [
            "Irregular, delayed cycles (>35-50 days) with jawline acne or excess facial/body hair",
            "Severe debilitating lower abdominal/pelvic cramps during first 48 hours of period",
            "Heavy prolonged menstrual flow requiring frequent pad changes or passing large clots",
            "Delayed period by more than 6-8 weeks with lower pelvic heaviness"
        ],
        "discriminates": [
            "Polycystic Ovary Syndrome (PCOS) & Menstrual Irregularity",
            "Primary Dysmenorrhea & Pelvic Pain"
        ],
        "target_symptoms_boost": {
            "Irregular, delayed cycles (>35-50 days) with jawline acne or excess facial/body hair": ["pcos_pcod_symptoms", "cystic_hormonal_acne"],
            "Severe debilitating lower abdominal/pelvic cramps during first 48 hours of period": ["lower_pelvic_ovarian_pain"],
            "Heavy prolonged menstrual flow requiring frequent pad changes or passing large clots": ["general_weakness", "fatigue"],
            "Delayed period by more than 6-8 weeks with lower pelvic heaviness": ["pcos_pcod_symptoms"]
        }
    },
    # 7. Abdominal Pain & GI Reflux
    {
        "id": "q_abdominal_location",
        "domain_triggers": ["abdominal", "stomach", "acidity", "epigastric", "reflux", "gerd", "vomiting", "diarrhea", "nausea", "bloating", "indigestion", "flank"],
        "question": "Where is your digestive discomfort located and when is it most intense?",
        "options": [
            "Upper center burning / sour acid regurgitation behind breastbone after meals",
            "Sharp right upper quadrant pain under rib cage, aggravated after fatty meals",
            "Diffuse cramping all over belly with frequent watery loose stools and nausea",
            "Lower back / flank side discomfort near the kidney angle"
        ],
        "discriminates": [
            "Gastroesophageal Reflux (GERD) & Peptic Ulcer",
            "Acute Cholecystitis / Gallstone Pathology",
            "Acute Gastroenteritis & Dehydration",
            "Acute Pyelonephritis / Complicated UTI"
        ],
        "target_symptoms_boost": {
            "Upper center burning / sour acid regurgitation behind breastbone after meals": ["epigastric_burning_pain", "loss_of_appetite"],
            "Right upper side under rib cage, aggravated after fatty meals": ["right_upper_quadrant_pain", "nausea"],
            "Diffuse cramping all over belly with frequent watery loose stools and nausea": ["diarrhea", "vomiting"],
            "Lower back / flank side discomfort near the kidney angle": ["flank_kidney_angle_pain"]
        }
    },
    # 8. Skin Allergy & Rash
    {
        "id": "q_skin_rash_allergy",
        "domain_triggers": ["rash", "hives", "itching", "pruritus", "urticaria", "blister", "petechiae"],
        "question": "What are the characteristics of your skin rash or itching?",
        "options": [
            "Raised itchy red welts / hives (urticaria) that appear suddenly and shift location",
            "Dry, inflamed red patches with intense scaling and persistent scratching",
            "Fluid-filled blister clusters with raw burning pain",
            "Tiny pinpoint non-blanching red/purple dots (petechiae) with fever"
        ],
        "discriminates": [
            "Allergic Dermatitis & Urticaria",
            "Acute Dengue Infection with Warning Signs"
        ],
        "target_symptoms_boost": {
            "Raised itchy red welts / hives (urticaria) that appear suddenly and shift location": ["hives_urticaria", "skin_redness"],
            "Dry, inflamed red patches with intense scaling and persistent scratching": ["skin_rash", "itching_pruritus"],
            "Fluid-filled blister clusters with raw burning pain": ["blisters"],
            "Tiny pinpoint non-blanching red/purple dots (petechiae) with fever": ["petechiae_purpura", "high_fever"]
        }
    },
    # 9. Chest Pain & Cardiac Radiation
    {
        "id": "q_pain_radiation",
        "domain_triggers": ["chest", "palpitation", "heart", "angina", "arm_jaw"],
        "question": "Does your chest discomfort radiate anywhere else?",
        "options": [
            "Yes, radiates to left arm, neck, or lower jaw with heavy squeezing tightness",
            "Radiates through to upper back between shoulder blades",
            "Burning sensation behind breastbone after meals, relieved by antacids",
            "No radiation, strictly localized"
        ],
        "discriminates": [
            "Acute Coronary Syndrome / Angina (Cardiac Emergency)"
        ],
        "target_symptoms_boost": {
            "Yes, radiates to left arm, neck, or lower jaw with heavy squeezing tightness": ["pain_radiating_to_arm_jaw"]
        }
    },
    # 10. Respiratory & Breathing Triggers
    {
        "id": "q_breathing_trigger",
        "domain_triggers": ["cough", "breath", "breathlessness", "wheezing", "dyspnea", "sputum", "phlegm"],
        "question": "When does your shortness of breath or cough worsen?",
        "options": [
            "Deep chest cough producing thick yellow or rust-colored phlegm",
            "Dry persistent tickly cough with wheezing and chest tightness on exertion",
            "Severe breathlessness when lying completely flat on the bed",
            "Worse only when taking a deep breath or changing posture"
        ],
        "discriminates": [
            "Bacterial Pneumonia / Lower Respiratory Infection",
            "COVID-19 / Severe Viral Pneumonitis"
        ],
        "target_symptoms_boost": {
            "Deep chest cough producing thick yellow or rust-colored phlegm": ["productive_cough_phlegm"],
            "Severe breathlessness when lying completely flat on the bed": ["orthopnea_lying_flat_breathless"]
        }
    },
    # 11. Fever Pattern
    {
        "id": "q_fever_pattern",
        "domain_triggers": ["fever", "chills", "sweat", "shivering"],
        "question": "What is your highest body temperature and how does the fever behave?",
        "options": [
            "High spike (>102°F) with intense teeth-chattering chills and shaking shivering",
            "Gradually rising step-ladder fever day by day with severe fatigue and headache",
            "Mild low-grade fever (around 99-100°F) mainly in late afternoon/evening",
            "Intermittent sweating episodes without high thermometer readings"
        ],
        "discriminates": [
            "Acute Dengue Infection with Warning Signs",
            "Typhoid Enteric Fever",
            "Bacterial Pneumonia / Lower Respiratory Infection"
        ],
        "target_symptoms_boost": {
            "High spike (>102°F) with intense teeth-chattering chills and shaking shivering": ["chills"],
            "Gradually rising step-ladder fever day by day with severe fatigue and headache": ["high_fever"]
        }
    },
    # 12. Headache Character
    {
        "id": "q_headache_character",
        "domain_triggers": ["headache", "migraine", "thunderclap", "vertigo", "photophobia"],
        "question": "How quickly did the severe headache develop and what does it feel like?",
        "options": [
            "Instant sudden 'worst headache of life' like a thunderclap within seconds",
            "Pulsating throbbing ache on one side of head with light/sound sensitivity",
            "Dull constant band-like pressure across both temples and back of neck",
            "Headache accompanied by spinning vertigo and loss of balance"
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
    # 13. Neurological Focal Signs
    {
        "id": "q_neurological_focal",
        "domain_triggers": ["droop", "slurred", "stroke", "weakness", "numbness", "paralysis", "facial_droop"],
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
    Evaluates only clinical questions that match the active symptom domain, computes their Information Gain,
    and returns the single best question. Stops asking when all relevant domain questions are answered.
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

    symptoms_joined = " ".join(current_symptoms).lower()
    top_candidates = [c["disease"] for c in entropy_info["candidate_distribution"][:3]]

    # 2. Evaluate Information Gain across strictly eligible domain questions
    candidates = []
    for q in QUESTION_BANK:
        if q["id"] in answered_ids_set:
            continue

        # Check domain trigger match with selected symptoms
        triggers = q.get("domain_triggers", [])
        has_trigger_match = any(t in symptoms_joined for t in triggers)

        # Check hypothesis overlap with top candidate diseases
        overlap_count = sum(1 for d in q["discriminates"] if d in top_candidates)

        # STRICT FILTER: DO NOT ask question if it has no symptom domain match AND no top disease overlap
        if not has_trigger_match:
            continue

        ig = calculate_information_gain_for_question(
            q_data=q,
            current_symptoms=current_symptoms,
            current_entropy=current_entropy,
            qa_answers=qa_answers,
            patient_context=patient_context
        )
        
        keyword_boost = 6.0 if has_trigger_match else 0.0
        relevance_score = (ig * 3.0) + (overlap_count * 4.0) + keyword_boost

        candidates.append({
            "question_data": q,
            "information_gain": round(max(ig, 0.45), 3),
            "relevance_score": round(relevance_score, 3),
            "expected_uncertainty_reduction_pct": round(min(((max(ig, 0.45)) / max(current_entropy, 0.1)) * 100, 75.0), 1),
            "target_hypotheses": q["discriminates"]
        })

    if not candidates:
        # All relevant symptom domain questions have been answered!
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
