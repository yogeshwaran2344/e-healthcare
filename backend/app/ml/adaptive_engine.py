"""
Adaptive Multi-Stage Question Engine, Context-Aware Bayesian Predictor,
3-Tier Risk Triage & Explainable AI (XAI).
"""

import math
from typing import List, Dict, Any, Optional
from .dataset import ALL_SYMPTOMS, DISEASES_DB
from .uncertainty_engine import calculate_disease_posteriors, compute_entropy_and_uncertainty, match_symptom_token
from .explainable_map_engine import generate_explainable_decision_map
from .test_optimization_engine import optimize_minimum_diagnostic_test_set

# Symptom-specific targeted clinical follow-up questions
SYMPTOM_SPECIFIC_QUESTIONS = {
    "hair_loss": {
        "triggers": ["hair", "scalp", "alopecia", "shedding", "thinning", "greying", "brittle"],
        "question": "How would you describe the pattern and progression of your hair loss or scalp problem?",
        "options": [
            "Sudden diffuse shedding all over the scalp (handfuls in brush/shower post-stress/fever)",
            "Gradual widening of parting line or thinning across the crown over months",
            "Smooth, round coin-sized bald patches appearing rapidly (patchy loss)",
            "Severe flaky dandruff with greasy yellowish buildup, scalp itching, and hair breakage"
        ]
    },
    "scalp_dermatitis": {
        "triggers": ["scalp", "dandruff", "itching", "folliculitis", "flaking", "bumps"],
        "question": "Describe your scalp sensations and root condition:",
        "options": [
            "Greasy yellowish crusts/flakes with intense itching, burning, and redness",
            "Dry powdery white dandruff without noticeable redness",
            "Tender, painful red bumps or small pustules at hair follicle bases",
            "Relatively normal scalp, but strands detach with minimal tension"
        ]
    },
    "facial_acne": {
        "triggers": ["acne", "face", "facial", "pimple", "cystic", "blackhead", "whitehead", "comedone"],
        "question": "What type of facial breakouts or blemishes are you predominantly experiencing?",
        "options": [
            "Deep, painful red cystic nodules along jawline, chin, and lower cheeks (hormonal)",
            "Surface blackheads, whiteheads, and oily shine across forehead and nose (T-zone)",
            "Small red pustules and pimples that flare up after certain sunscreens or cosmetics",
            "Stubborn post-acne dark marks, hyperpigmentation, and uneven texture"
        ]
    },
    "facial_sensitivity_rosacea": {
        "triggers": ["rosacea", "face", "facial", "redness", "peeling", "oily", "grease"],
        "question": "How does your facial skin react to environment, temperature, and skincare products?",
        "options": [
            "Becomes excessively oily and greasy within 2-3 hours of cleansing",
            "Flushes bright red and stings with sun exposure, hot drinks, spicy food, or skincare",
            "Feels tight, flaky, dry, and sensitive despite regular moisturizing",
            "Breakout flares correlate directly with monthly menstrual period dates"
        ]
    },
    "period_menstrual": {
        "triggers": ["period", "menstrual", "pcos", "pcod", "cramp", "pelvic", "ovarian"],
        "question": "Describe your menstrual cycle regularity and associated hormonal features:",
        "options": [
            "Irregular or delayed cycles (>35-50 days) with jawline acne or excess facial hair",
            "Severe debilitating lower pelvic and ovarian cramps during first 48 hours of period",
            "Extremely heavy menstrual flow requiring frequent pad changes or passing clots",
            "Delayed period by more than 6-8 weeks with lower pelvic heaviness"
        ]
    },
    "gastro_abdominal": {
        "triggers": ["abdominal", "stomach", "acidity", "epigastric", "reflux", "gerd", "vomiting", "diarrhea", "nausea", "bloating", "indigestion"],
        "question": "Where is your digestive discomfort located and when is it most intense?",
        "options": [
            "Upper center burning / sour acid fluid regurgitation behind breastbone after meals",
            "Sharp right upper quadrant pain under ribs, worse after fatty foods",
            "Generalized cramping all over belly with watery loose stools and nausea",
            "Relieved temporarily after eating, but returns 2-3 hours later or at night"
        ]
    },
    "skin_rash_allergy": {
        "triggers": ["rash", "hives", "itching", "pruritus", "urticaria", "blister", "petechiae", "skin"],
        "question": "Describe the appearance and onset of your skin rash or itching:",
        "options": [
            "Raised itchy red welts / hives (urticaria) that appear suddenly and shift location",
            "Dry, inflamed red patches with intense scaling, roughness, and continuous scratching",
            "Fluid-filled blister clusters with raw burning pain",
            "Tiny pinpoint non-blanching red/purple spots (petechiae) with high fever"
        ]
    },
    "chest_cardiac": {
        "triggers": ["chest", "palpitation", "heart", "angina"],
        "question": "Describe your chest sensations and any radiation:",
        "options": [
            "Heavy squeezing pressure in center of chest radiating to left arm or jaw",
            "Sharp localized pain that worsens when breathing in deeply or coughing",
            "Rapid fluttering / pounding palpitations with lightheadedness",
            "Burning retrosternal chest sensation after eating or lying down"
        ]
    },
    "cough_respiratory": {
        "triggers": ["cough", "breath", "breathlessness", "wheezing", "sputum", "phlegm"],
        "question": "Describe your cough and breathing difficulty:",
        "options": [
            "Deep chest cough producing thick yellow or rust-colored phlegm",
            "Dry persistent tickly cough with wheezing and chest tightness",
            "Shortness of breath on mild exertion or when lying flat in bed",
            "Barking dry cough accompanied by throat tickle and runny nose"
        ]
    },
    "headache_neuro": {
        "triggers": ["headache", "migraine", "thunderclap", "vertigo", "photophobia", "dizziness"],
        "question": "Characterize your headache onset and sensations:",
        "options": [
            "Sudden explosive 'thunderclap' headache reaching maximum agony within seconds",
            "Pulsating throbbing pain on one side of head with sensitivity to light and sound",
            "Dull constant tight-band pressure around forehead and back of neck",
            "Headache accompanied by spinning vertigo, nausea, and unsteady balance"
        ]
    },
    "fever_infection": {
        "triggers": ["fever", "chills", "sweat"],
        "question": "What is your highest body temperature and how does the fever behave?",
        "options": [
            "High spike (>102°F) with intense teeth-chattering chills and shaking shivering",
            "Gradually rising step-ladder fever day by day with severe fatigue and headache",
            "Mild low-grade fever (around 99-100°F) mainly in late afternoon/evening",
            "Intermittent sweating episodes without high thermometer readings"
        ]
    }
}

def generate_adaptive_questions(selected_symptoms: List[str], patient_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Dynamically generates clinical follow-up questions tailored directly to the selected symptoms.
    Targeted symptom inquiries appear first, followed by clinical duration, severity, and prior remedies.
    """
    questions = []
    symptoms_joined = " ".join(selected_symptoms).lower()
    matched_keys = set()
    
    # 1. Targeted Symptom-Specific Questions (Prioritized First)
    for key, q_data in SYMPTOM_SPECIFIC_QUESTIONS.items():
        triggers = q_data.get("triggers", [key])
        if any(t in symptoms_joined for t in triggers) and key not in matched_keys:
            questions.append({
                "id": f"specific_{key}",
                "question": q_data["question"],
                "type": "select",
                "options": q_data["options"]
            })
            matched_keys.add(key)
            if len(questions) >= 3:
                break

    # 2. Onset & Duration (Standard Clinical inquiry)
    questions.append({
        "id": "duration_days",
        "question": "How many days or weeks have you been experiencing these primary symptoms?",
        "type": "select",
        "options": [
            "1-2 days (acute onset)",
            "3-7 days (persistent)",
            "1-3 weeks",
            "More than a month (chronic / progressive)"
        ]
    })

    # 3. Pain / Severity Intensity Rating (Numeric Rating Scale 1-10)
    questions.append({
        "id": "severity_scale",
        "question": "On a scale from 1 (mild) to 10 (unbearable), how severe is your overall discomfort?",
        "type": "select",
        "options": [
            "1 - 3 (Mild, able to do normal daily activities)",
            "4 - 6 (Moderate, interfering with work, skin comfort, or sleep)",
            "7 - 8 (Severe, causing significant distress or painful flare)",
            "9 - 10 (Extreme, unbearable agony or acute distress)"
        ]
    })

    # 4. Medication & Pre-existing Context
    questions.append({
        "id": "prior_meds_taken",
        "question": "Have you taken any home remedies, topical applications, or over-the-counter medications for this?",
        "type": "select",
        "options": [
            "None yet",
            "Topical creams / medicated shampoos / skin serums",
            "Paracetamol / Painkillers (Ibuprofen / Aspirin)",
            "Antacids / Digestion tablets",
            "Prescription antibiotics / hormonal pills"
        ]
    })

    return questions


def get_recommended_report_types(
    symptoms: List[str],
    qa_answers: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Determines context-aware diagnostic upload options and clinical necessity
    strictly based on selected symptoms and reported severity/duration.
    Prevents irrelevant prompts (e.g., Chest X-Ray or CBC for mild acne).
    """
    qa_answers = qa_answers or {}
    symptoms_lower = [s.lower() for s in (symptoms or [])]
    symptoms_joined = " ".join(symptoms_lower)
    severity_ans = str(qa_answers.get("severity_scale", "")).lower()
    duration_ans = str(qa_answers.get("duration_days", "")).lower()
    qa_blob = " ".join(str(v) for v in qa_answers.values()).lower()

    is_severe = ("7 - 8" in severity_ans) or ("9 - 10" in severity_ans) or ("severe" in severity_ans) or ("extreme" in severity_ans)
    is_moderate = ("4 - 6" in severity_ans) or ("moderate" in severity_ans)
    is_chronic = ("month" in duration_ans) or ("1-3 weeks" in duration_ans)

    if is_severe:
        severity_tier = "Severe / Acute"
    elif is_moderate or is_chronic:
        severity_tier = "Moderate / Persistent"
    else:
        severity_tier = "Mild"

    def item(value: str, why: str, label: Optional[str] = None) -> Dict[str, str]:
        return {"value": value, "label": label or value, "why": why}

    has_cardiac = any(k in symptoms_joined for k in ["sharp_chest_pain", "pain_radiating", "palpitations", "angina"])
    has_respiratory = any(k in symptoms_joined for k in ["breathlessness", "wheezing", "chest_tightness", "cough", "sputum", "phlegm"])
    has_neuro_red = any(k in symptoms_joined for k in ["thunderclap", "facial_droop", "limb_weakness", "slurred_speech", "stiff_neck"])
    has_gastro = any(k in symptoms_joined for k in ["abdominal", "stomach", "epigastric", "acidity", "vomiting", "diarrhea", "jaundice", "dark_urine", "indigestion"])
    has_gyno = any(k in symptoms_joined for k in ["period", "menstrual", "pcos", "pelvic", "ovarian", "vaginal"])
    has_urinary = any(k in symptoms_joined for k in ["flank", "dysuria", "hematuria", "urinary"])
    has_fever = any(k in symptoms_joined for k in ["high_fever", "fever", "chills", "petechiae"])
    has_acne = any(k in symptoms_joined for k in ["acne", "pimple", "blackhead", "whitehead", "oily_skin", "post_acne", "rosacea", "dry_peeling_skin"])
    has_hair = any(k in symptoms_joined for k in ["hair", "scalp", "dandruff", "alopecia"])
    has_skin_rash = any(k in symptoms_joined for k in ["skin_rash", "hives", "urticaria", "itching_pruritus", "blisters", "skin_redness"])
    has_joint = any(k in symptoms_joined for k in ["joint", "arthritis", "swelling_in_legs", "calf_tenderness"])
    has_headache = any(k in symptoms_joined for k in ["headache", "migraine", "vertigo", "photophobia", "dizziness"])

    # 1. Cardiac / Acute Neurological / Severe Respiratory always take safety priority
    if has_cardiac:
        return {
            "reports_needed": True,
            "requirement_level": "URGENT_RECOMMENDED",
            "clinical_domain": "Cardiology & Vascular Assessment",
            "severity_tier": severity_tier,
            "banner_title": "Cardiac Diagnostic Reports Recommended (If Available)",
            "banner_message": "Because cardiac/chest symptoms were selected, ECG, Troponin, or recent BP/Lipid logs are highly relevant. Do not delay emergency care to upload files.",
            "recommended_report_types": [
                item("12-Lead ECG Report", "Detects myocardial ischemia, rhythm blocks, or acute arrhythmia."),
                item("Cardiac Troponin-I / Lipid Panel", "Checks myocardial injury biomarkers and cardiovascular risk."),
                item("Chest X-Ray", "Evaluates cardiac silhouette and pulmonary congestion."),
                item("Complete Blood Count (CBC)", "Baseline anemia and systemic infection screening."),
                item("Other Diagnostic Document", "Any prior cardiology consultation or stress test.")
            ]
        }

    if has_neuro_red or (has_headache and is_severe):
        return {
            "reports_needed": True,
            "requirement_level": "RECOMMENDED" if not has_neuro_red else "URGENT_RECOMMENDED",
            "clinical_domain": "Neurology & Neuro-Vascular Care",
            "severity_tier": severity_tier,
            "banner_title": "Neurological Scan / Vitals Workup (Severe Headache / Red-Flag Symptoms)",
            "banner_message": "For severe or sudden neurological symptoms, prior Brain CT/MRI scans or Blood Pressure logs assist rapid specialist review.",
            "recommended_report_types": [
                item("Brain CT Scan", "Rules out acute hemorrhage or structural mass effect."),
                item("Brain MRI", "Detailed vascular and parenchymal brain evaluation."),
                item("Vitals / Blood Pressure Log", "Checks hypertensive spikes triggering severe headache."),
                item("Complete Blood Count (CBC)", "Screens for systemic inflammation or infection."),
                item("Other Diagnostic Document", "Previous neurology prescription or eye exam report.")
            ]
        }

    # 2. Acne & Facial Dermatology (without systemic infection/red flags)
    if has_acne and not (has_respiratory or has_fever or has_gastro or has_gyno):
        is_cystic_or_hormonal = ("cystic" in symptoms_joined) or ("hormonal" in qa_blob) or ("menstrual" in qa_blob)
        if not is_severe and not is_moderate and not is_cystic_or_hormonal:
            return {
                "reports_needed": False,
                "requirement_level": "NOT_REQUIRED",
                "clinical_domain": "Dermatology (Acne & Facial Skin)",
                "severity_tier": severity_tier,
                "banner_title": "No Lab Blood Tests, X-Rays, or Scans Needed",
                "banner_message": (
                    "For mild/surface acne or facial skincare concerns, X-rays, CT scans, and routine CBC blood tests are NOT required. "
                    "You can skip directly to Health Triage, or optionally upload a clear photo of the affected area or skincare prescription."
                ),
                "recommended_report_types": [
                    item("Skin / Acne Lesion Photo", "Optional visual reference for dermatologist review (no radiation or blood draw needed)."),
                    item("Dermatology Prescription / Skincare Record", "Optional record of topical creams, cleansers, or prior treatments."),
                    item("Other Diagnostic Document", "Any other relevant dermatology note.")
                ]
            }
        else:
            return {
                "reports_needed": False,
                "requirement_level": "OPTIONAL_TARGETED",
                "clinical_domain": "Dermatology (Persistent / Cystic Acne)",
                "severity_tier": severity_tier,
                "banner_title": "X-Rays & Routine CBC Not Needed — Optional Acne / Hormonal Workup",
                "banner_message": (
                    "Chest X-rays and CT scans are never needed for acne. For persistent, moderate-to-severe, or cystic jawline breakouts, "
                    "only a clear lesion photo or a targeted Hormone/LFT panel (if on prescription isotretinoin/PCOS workup) is relevant."
                ),
                "recommended_report_types": [
                    item("Skin / Acne Lesion Photo", "Helps the dermatologist grade comedonal vs cystic inflammation severity."),
                    item("Female Hormone Panel (PCOS / Testosterone / DHEA-S)", "Helpful only if cystic jawline acne is linked to irregular cycles or hormonal imbalance."),
                    item("Liver Function Test (LFT)", "Relevant only if monitoring baseline liver enzymes before/during oral isotretinoin therapy."),
                    item("Dermatology Prescription / Skincare Record", "Share active retinoid, benzoyl peroxide, or antibiotic cream history."),
                    item("Other Diagnostic Document", "Any other dermatology evaluation.")
                ]
            }

    # 3. Hair & Scalp
    if has_hair and not (has_fever or has_respiratory or has_gastro):
        opts = [
            item("Scalp / Hair Density Photo", "Visualizes thinning pattern, scalp flaking, or patchy hair loss."),
            item("Serum Ferritin & Iron Studies", "Evaluates iron stores — a primary driver of telogen effluvium hair fall."),
            item("Thyroid (TSH) & Vitamin D3 / B12 Panel", "Checks common nutritional and endocrine triggers of hair shedding.")
        ]
        if is_severe or is_moderate:
            opts.append(item("Complete Blood Count (CBC)", "Checks hemoglobin levels for anemia-related hair thinning."))
        opts.append(item("Other Diagnostic Document", "Trichoscopy or prior dermatology note."))
        return {
            "reports_needed": is_severe or is_chronic,
            "requirement_level": "OPTIONAL_TARGETED" if (is_severe or is_chronic or is_moderate) else "NOT_REQUIRED",
            "clinical_domain": "Trichology & Scalp Care",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Hair & Scalp Workup (No X-Ray / CT Needed)",
            "banner_message": "Imaging scans are unnecessary for hair or scalp concerns. Ferritin, Thyroid/Vitamin levels, or a scalp photo are most useful if available.",
            "recommended_report_types": opts
        }

    # 4. Gynaecology & Women's Health
    if has_gyno:
        return {
            "reports_needed": is_moderate or is_severe or is_chronic,
            "requirement_level": "RECOMMENDED" if (is_moderate or is_severe or is_chronic) else "OPTIONAL_TARGETED",
            "clinical_domain": "Gynaecology & Reproductive Health",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Gynaecological & Hormonal Reports",
            "banner_message": "For menstrual irregularity, PCOS, or pelvic symptoms, Pelvic Ultrasound and Hormone Panels provide key diagnostic clarity (no chest imaging needed).",
            "recommended_report_types": [
                item("Pelvic Ultrasound (USG Pelvis)", "Evaluates ovarian morphology, cysts, and endometrial thickness."),
                item("Female Hormone Panel (LH / FSH / Testosterone / TSH)", "Profiles ovulatory, androgen, and thyroid balance."),
                item("Complete Blood Count (CBC)", "Checks hemoglobin for anemia especially with heavy menstrual bleeding."),
                item("Other Diagnostic Document", "Prior gynaecology consultation or prescription.")
            ]
        }

    # 5. Skin Rash / Allergy
    if has_skin_rash and not (has_fever or "petechiae" in symptoms_joined):
        opts = [
            item("Skin Rash / Hives Photo", "Captures rash distribution and morphology before lesions fade."),
            item("Allergy / IgE Panel", "Identifies allergen sensitization if chronic or recurrent."),
            item("Other Diagnostic Document", "Prior dermatology prescription or patch test.")
        ]
        if is_severe:
            opts.insert(2, item("Complete Blood Count (CBC)", "Evaluates eosinophils and inflammatory response in severe flares."))
        return {
            "reports_needed": False,
            "requirement_level": "OPTIONAL_TARGETED" if is_severe else "NOT_REQUIRED",
            "clinical_domain": "Dermatology & Allergy",
            "severity_tier": severity_tier,
            "banner_title": "Skin Photo Optional — Lab Tests Not Required for Mild Rashes",
            "banner_message": "Routine blood tests or scans are not needed for mild skin rashes/hives. Uploading a clear photo helps clinical assessment.",
            "recommended_report_types": opts
        }

    # 6. Respiratory / Cough
    if has_respiratory:
        if not is_severe and not is_moderate and "breathlessness" not in symptoms_joined:
            return {
                "reports_needed": False,
                "requirement_level": "NOT_REQUIRED",
                "clinical_domain": "Upper Respiratory / Mild Cough",
                "severity_tier": severity_tier,
                "banner_title": "No Chest X-Ray or CT Scan Required for Mild Cold/Cough",
                "banner_message": "For mild acute cough without shortness of breath, imaging is unnecessary. You can skip directly to Health Triage or attach a viral test if already done.",
                "recommended_report_types": [
                    item("RT-PCR Viral Panel (COVID / Influenza)", "Optional viral swab confirmation if already tested."),
                    item("Vitals / SpO2 & Temperature Log", "Optional oxygen saturation and fever reading."),
                    item("Other Diagnostic Document", "Previous physician note.")
                ]
            }
        opts = [
            item("Chest X-Ray", "Screens lung fields for consolidation, pneumonia, or effusion."),
            item("Complete Blood Count (CBC)", "Assesses WBC count to differentiate bacterial vs viral infection."),
            item("RT-PCR Viral Panel (COVID / Influenza)", "Identifies specific respiratory viral pathogens."),
        ]
        if is_severe or "breathlessness" in symptoms_joined:
            opts.append(item("CT Scan", "High-resolution CT chest if severe hypoxia or complex pneumonia is suspected."))
        opts.append(item("Other Diagnostic Document", "Spirometry, SpO2 log, or pulmonology note."))
        return {
            "reports_needed": True,
            "requirement_level": "RECOMMENDED",
            "clinical_domain": "Pulmonology & Respiratory Medicine",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Respiratory & Lung Evaluation Reports",
            "banner_message": "Because persistent/moderate-to-severe cough or breathlessness was reported, a Chest X-Ray, CBC, or Viral Panel can meaningfully refine diagnosis.",
            "recommended_report_types": opts
        }

    # 7. Gastrointestinal / Liver
    if has_gastro:
        if not is_severe and not is_moderate and not any(k in symptoms_joined for k in ["jaundice", "dark_urine", "right_upper"]):
            return {
                "reports_needed": False,
                "requirement_level": "NOT_REQUIRED",
                "clinical_domain": "Digestive Care (Mild Acidity / Stomach)",
                "severity_tier": severity_tier,
                "banner_title": "No Scans or Blood Tests Required for Mild Digestive Discomfort",
                "banner_message": "For mild acidity or brief stomach upset, CT scans and X-rays are not needed. Skip directly to Health Triage unless you already have a gastro report.",
                "recommended_report_types": [
                    item("Other Diagnostic Document", "Optional prior endoscopy, prescription, or H. pylori report."),
                    item("Liver Function Test (LFT)", "Only if advised for persistent upper abdominal discomfort.")
                ]
            }
        return {
            "reports_needed": True,
            "requirement_level": "RECOMMENDED",
            "clinical_domain": "Gastroenterology & Hepatology",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Gastro & Liver Function Reports",
            "banner_message": "For moderate/severe abdominal pain, vomiting, or jaundice indicators, LFT, Abdominal Ultrasound, or CBC are most informative (no Chest X-Ray needed).",
            "recommended_report_types": [
                item("Liver Function Test (LFT)", "Checks bilirubin, SGOT/SGPT, and hepatobiliary enzymes."),
                item("Abdominal Ultrasound (USG)", "Evaluates gallbladder, liver, appendix, and abdominal organs."),
                item("Complete Blood Count (CBC)", "Screens for acute abdominal infection or anemia."),
                item("Other Diagnostic Document", "Endoscopy, stool test, or gastro prescription.")
            ]
        }

    # 8. Urinary / Kidney
    if has_urinary:
        return {
            "reports_needed": True,
            "requirement_level": "RECOMMENDED",
            "clinical_domain": "Urology & Nephrology",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Urinary & Kidney Reports",
            "banner_message": "Urinalysis and Renal Function (KFT) directly evaluate urinary infections or kidney stone risk.",
            "recommended_report_types": [
                item("Urinalysis Routine & Culture (Urine R/M)", "Detects pus cells, nitrites, bacteria, or microscopic hematuria."),
                item("Kidney Function Test (KFT / Creatinine)", "Measures serum creatinine, urea, and electrolytes."),
                item("Abdominal Ultrasound (USG)", "Checks kidneys and bladder for calculi or obstruction."),
                item("Complete Blood Count (CBC)", "Evaluates systemic infection response."),
                item("Other Diagnostic Document", "Any prior urology report.")
            ]
        }

    # 9. Fever / Systemic Infection
    if has_fever or "petechiae" in symptoms_joined:
        return {
            "reports_needed": is_moderate or is_severe or is_chronic or ("petechiae" in symptoms_joined),
            "requirement_level": "RECOMMENDED" if (is_moderate or is_severe or is_chronic) else "OPTIONAL_TARGETED",
            "clinical_domain": "Systemic Febrile & Infection Workup",
            "severity_tier": severity_tier,
            "banner_title": "Febrile Blood & Serology Panel (If Available)",
            "banner_message": "For fever workup, CBC (platelets & WBC), Dengue/Malaria antigen tests, or LFT help distinguish viral vs bacterial causes.",
            "recommended_report_types": [
                item("Complete Blood Count (CBC)", "Critical for checking Platelet count, WBC/leukocytes, and hemoglobin."),
                item("Dengue / Malaria / Typhoid Panel", "Rapid serology for endemic causes of acute fever."),
                item("Liver Function Test (LFT)", "Helpful if fever accompanies jaundice, nausea, or dengue suspicion."),
                item("Other Diagnostic Document", "Temperature log or prior clinic note.")
            ]
        }

    # 10. Musculoskeletal / Joint Pain
    if has_joint:
        return {
            "reports_needed": is_severe or is_chronic,
            "requirement_level": "OPTIONAL_TARGETED" if (is_severe or is_chronic) else "NOT_REQUIRED",
            "clinical_domain": "Orthopedics & Rheumatology",
            "severity_tier": severity_tier,
            "banner_title": "Targeted Joint & Inflammatory Workup" if (is_severe or is_chronic) else "No Lab Tests Required for Mild Joint Strain",
            "banner_message": "Mild soreness does not require scans. For persistent or severe joint swelling, Joint X-ray or RF/CRP/Uric Acid panels are relevant.",
            "recommended_report_types": [
                item("Joint / Musculoskeletal X-Ray", "Evaluates joint space narrowing, fractures, or structural wear."),
                item("CRP / Rheumatoid Factor / Uric Acid Panel", "Screens for inflammatory arthritis or gout."),
                item("Complete Blood Count (CBC)", "Baseline inflammatory screening."),
                item("Other Diagnostic Document", "Orthopedic consultation or physiotherapy note.")
            ]
        }

    # 11. Mild Headache without red flags
    if has_headache:
        return {
            "reports_needed": False,
            "requirement_level": "NOT_REQUIRED",
            "clinical_domain": "Headache & Migraine Care",
            "severity_tier": severity_tier,
            "banner_title": "No Scans or Blood Tests Required for Mild/Moderate Headache",
            "banner_message": "Routine Brain CT/MRI or CBC are not required for mild uncomplicated headaches. You may skip directly to Health Triage or upload a BP log if measured.",
            "recommended_report_types": [
                item("Vitals / Blood Pressure Log", "Checks if blood pressure fluctuations correlate with headache episodes."),
                item("Other Diagnostic Document", "Eye/vision checkup or prior migraine prescription.")
            ]
        }

    # 12. General Fallback (Respects severity!)
    if not is_severe and not is_moderate:
        return {
            "reports_needed": False,
            "requirement_level": "NOT_REQUIRED",
            "clinical_domain": "Primary Care & Wellness",
            "severity_tier": severity_tier,
            "banner_title": "Reports Optional for Mild Symptoms",
            "banner_message": "For mild symptoms, diagnostic scans and lab panels are generally unnecessary. Skip directly to Health Triage or attach an existing record if available.",
            "recommended_report_types": [
                item("Vitals / Health Checkup Summary", "Recent BP, Heart Rate, Blood Sugar, or SpO2 measurement."),
                item("Complete Blood Count (CBC)", "Optional general baseline blood screening."),
                item("Other Diagnostic Document", "Any existing prescription or medical document.")
            ]
        }

    return {
        "reports_needed": True,
        "requirement_level": "OPTIONAL_TARGETED",
        "clinical_domain": "General Internal Medicine",
        "severity_tier": severity_tier,
        "banner_title": "Relevant Clinical Reports (Optional Based on Severity)",
        "banner_message": "Because moderate-to-severe or persistent symptoms were reported, uploading relevant lab results improves triage precision.",
        "recommended_report_types": [
            item("Complete Blood Count (CBC)", "Baseline infection, hemoglobin, and platelet assessment."),
            item("Vitals / Health Checkup Summary", "Blood pressure, blood glucose, and general metabolic screen."),
            item("Liver Function Test (LFT)", "Hepatic enzyme screening if systemic malaise is present."),
            item("Other Diagnostic Document", "Any scan or consultation document.")
        ]
    }

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

def resolve_broad_specialist(top_disease: str, symptoms: List[str]) -> Dict[str, str]:
    """
    Assigns the exact broad clinical medical specialty based on organ domain and symptoms.
    Guarantees that stomach/GI/liver issues route to Gastroenterologists & Hepatologists,
    chest/heart to Cardiologists, lungs/breathing to Pulmonologists, skin/hair/acne to Dermatologists/Trichologists,
    periods/PCOS/gynac to Gynecologists, urinary/kidney to Urologists/Nephrologists, etc.
    """
    symptoms_joined = " ".join(symptoms).lower()
    disease_lower = (top_disease or "").lower()

    # 1. Stomach, GI, Liver, Gallbladder, Acid Reflux, Bowel
    if any(k in disease_lower for k in ["gastro", "ulcer", "cholecyst", "stomach", "enteric", "typhoid", "liver", "hepatic", "jaundice", "gallstone", "pancreat", "bowel", "diarrhea", "acidity", "reflux", "gerd", "crohn", "colitis", "gastritis"]) or \
       any(k in symptoms_joined for k in ["abdominal", "stomach", "epigastric", "acidity", "vomiting", "diarrhea", "jaundice", "dark_urine", "nausea", "bloating", "indigestion", "loose_motion", "constipation", "hematemesis"]):
        return {
            "specialist": "Gastroenterologist & Hepatologist",
            "domain": "Digestive Health & Hepatology",
            "rationale": "Directly evaluates stomach mucosa, gastric acid secretion, intestinal absorption, liver function, and biliary tract pathology."
        }

    # 2. Cardiovascular, Chest Pain, Palpitations, Blood Pressure
    if any(k in disease_lower for k in ["coronary", "cardiac", "angina", "infarction", "arrhythmia", "hypertension", "heart"]) or \
       any(k in symptoms_joined for k in ["sharp_chest_pain", "palpitations", "radiating_to_arm", "angina", "cold_clammy", "syncope"]):
        return {
            "specialist": "Cardiologist (Interventional / Clinical)",
            "domain": "Cardiology & Vascular Medicine",
            "rationale": "Specializes in coronary perfusion, myocardial ischemia, rhythm disturbances, and acute cardiovascular risk management."
        }

    # 3. Respiratory, Lungs, Cough, Wheezing, Dyspnea
    if any(k in disease_lower for k in ["pneumonia", "covid", "bronch", "asthma", "pulmon", "respiratory", "pleur"]) or \
       any(k in symptoms_joined for k in ["cough", "breathlessness", "wheezing", "chest_tightness", "stridor", "hemoptysis"]):
        return {
            "specialist": "Pulmonologist (Chest Physician)",
            "domain": "Pulmonology & Respiratory Medicine",
            "rationale": "Specialized diagnosis and treatment of airway obstruction, lung parenchyma consolidation, and oxygen saturation dynamics."
        }

    # 4. Gynaecology, Women's Health, Periods, PCOS, Pelvic
    if any(k in disease_lower for k in ["pcos", "pcod", "dysmenorrhea", "ovarian", "uterine", "gynac", "pregnancy", "menopause", "endometri"]) or \
       any(k in symptoms_joined for k in ["period", "menstrual", "pcos", "pelvic", "vaginal", "ovarian", "breast_pain", "hot_flashes"]):
        return {
            "specialist": "Gynecologist & Obstetrician",
            "domain": "Obstetrics, Gynaecology & Reproductive Health",
            "rationale": "Focused management of hormonal ovulatory cycles, pelvic structures, endometrial health, and reproductive wellbeing."
        }

    # 5. Dermatology, Hair, Scalp, Acne, Skin
    if any(k in disease_lower for k in ["dermat", "acne", "hair", "scalp", "alopecia", "effluvium", "eczema", "psoriasis", "urticaria", "rash"]) or \
       any(k in symptoms_joined for k in ["acne", "hair", "scalp", "dandruff", "pimples", "rash", "hives", "itching", "alopecia", "skin_redness"]):
        return {
            "specialist": "Dermatologist & Trichologist",
            "domain": "Dermatology & Scalp Disorders",
            "rationale": "Expert clinical evaluation of cutaneous barrier function, follicular health, sebum gland regulation, and skin allergy pathways."
        }

    # 6. Neurological, Brain, Stroke, Migraine, Vertigo, Nerves
    if any(k in disease_lower for k in ["stroke", "migraine", "cerebrovascular", "headache", "neuro", "seizure", "epilepsy", "meningitis"]) or \
       any(k in symptoms_joined for k in ["thunderclap", "facial_droop", "limb_weakness", "slurred_speech", "vertigo", "photophobia", "stiff_neck", "confusion", "severe_headache"]):
        return {
            "specialist": "Neurologist",
            "domain": "Neurology & Neuro-vascular Disorders",
            "rationale": "Targeted neurological localization of central/peripheral nervous system abnormalities, vascular perfusion, and cephalalgia triggers."
        }

    # 7. Urology & Nephrology, Kidney, Urinary, Flank
    if any(k in disease_lower for k in ["pyelonephritis", "uti", "urinary", "renal", "kidney", "nephro", "urol", "calculus", "stone"]) or \
       any(k in symptoms_joined for k in ["flank", "dysuria", "urinary", "hematuria", "kidney"]):
        return {
            "specialist": "Urologist & Nephrologist",
            "domain": "Urology & Renal Medicine",
            "rationale": "Specialized assessment of glomerular filtration, urinary tract infection, and renal parenchymal integrity."
        }

    # 8. Orthopedics & Rheumatology, Joints, Bones, Arthritis
    if any(k in disease_lower for k in ["arthrit", "rheumat", "joint", "bone", "ortho", "gout", "spondyl"]) or \
       any(k in symptoms_joined for k in ["joint_pain", "morning_joint_stiffness", "swelling_in_legs", "calf_tenderness"]):
        return {
            "specialist": "Orthopedic Specialist & Rheumatologist",
            "domain": "Musculoskeletal & Rheumatic Disorders",
            "rationale": "Provides targeted clinical care for synovial inflammation, autoimmune joint damage, and biomechanical structural integrity."
        }

    # 9. Infectious Disease / Fevers
    if any(k in disease_lower for k in ["dengue", "malaria", "typhoid", "sepsis", "viral", "infection"]) or \
       any(k in symptoms_joined for k in ["high_fever", "fever", "chills", "petechiae"]):
        return {
            "specialist": "Infectious Disease Specialist & Internal Medicine",
            "domain": "Infectious Diseases & Internal Medicine",
            "rationale": "Specialized investigation of pathogen dynamics, serological markers, and systemic febrile syndromic care."
        }

    # Fallback
    top_info = DISEASES_DB.get(top_disease, {})
    fallback_specialist = top_info.get("specialist", "General Physician / Internal Medicine")
    return {
        "specialist": fallback_specialist,
        "domain": "Internal Medicine & Primary Care",
        "rationale": "Comprehensive systemic evaluation and holistic initial diagnostic workup."
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
    
    # Biomarker hints
    biomarker_keywords = " ".join(biomarkers.get("abnormal_flags", [])).lower()
    pre_existing_str = str(patient_context.get("pre_existing_conditions", "")).lower()

    # Closed-Loop Dynamic Adaptive Intelligence Integration
    posteriors = calculate_disease_posteriors(symptoms, qa_answers, patient_context, biomarkers)
    entropy_uncertainty = compute_entropy_and_uncertainty(posteriors)
    
    candidate_list = [{"disease": d, "probability": p} for d, p in posteriors.items()]
    candidate_list.sort(key=lambda x: x["probability"], reverse=True)
    
    top = candidate_list[0]
    top_disease = top["disease"]
    top_prob = top["probability"]
    top_info = DISEASES_DB.get(top_disease, {})

    # Broad specialist assignment tailored by domain & organ system
    specialist_res = resolve_broad_specialist(top_disease, symptoms)

    # Dynamic calibrated confidence: calculated directly from Bayesian posterior probability
    qa_bonus = min(len(qa_answers) * 3.5, 14.0) if qa_answers else 0.0
    biomarker_bonus = 12.0 if biomarkers.get("abnormal_flags") else 0.0
    raw_confidence = (top_prob * 100 * 1.55) + qa_bonus + biomarker_bonus
    confidence = round(min(max(raw_confidence, 42.0), 96.8), 1)

    # Explainable XAI factors derived dynamically from matched symptoms
    xai_factors = []
    matched_symptoms = []
    for s in symptoms:
        for ds in top_info.get("symptoms", []):
            if match_symptom_token(s, ds) >= 0.7:
                matched_symptoms.append(s.replace('_', ' '))
                break
    if matched_symptoms:
        xai_factors.append(f"Matched {len(matched_symptoms)} core clinical features: {', '.join(set(matched_symptoms))}.")

    # Biomarker synergy boosts
    if "platelet" in biomarker_keywords and "dengue" in top_disease.lower():
        xai_factors.append("Uploaded lab report confirms thrombocytopenia (low platelets), strongly elevating Dengue suspicion.")
    elif "wbc" in biomarker_keywords and ("pneumonia" in top_disease.lower() or "infection" in top_disease.lower()):
        xai_factors.append("Elevated white blood cell count (leukocytosis) in uploaded report indicates active bacterial infection.")
    elif "bilirubin" in biomarker_keywords and ("jaundice" in top_disease.lower() or "cholecystitis" in top_disease.lower()):
        xai_factors.append("Elevated total serum bilirubin in lab panel directly supports hepatic/biliary pathology.")
    elif ("infiltrate" in biomarker_keywords or "opacity" in biomarker_keywords) and "pneumonia" in top_disease.lower():
        xai_factors.append("Radiology/Chest scan findings show lung opacity consistent with pneumonia consolidation.")

    # Patient history synergy boosts
    if "diabetes" in pre_existing_str and ("pneumonia" in top_disease.lower() or "covid" in top_disease.lower()):
        xai_factors.append("Pre-existing Diabetes increases vulnerability to lower respiratory tract infections.")
    if ("hypertension" in pre_existing_str or "heart" in pre_existing_str) and "cardiac" in top_disease.lower():
        xai_factors.append("Documented cardiovascular medical history compounds risk of acute coronary syndrome.")

    if not xai_factors:
        xai_factors.append(f"Clinical symptom presentation correlates with {top_disease}.")

    # Differential diagnoses with domain specialist mapping
    alternatives = []
    for alt in candidate_list[1:4]:
        if alt["probability"] > 0.05:
            alt_info = DISEASES_DB.get(alt["disease"], {})
            alt_spec = resolve_broad_specialist(alt["disease"], symptoms)
            alternatives.append({
                "disease": alt["disease"],
                "confidence_percentage": round(min(alt["probability"] * 100 * 1.3, 85.0), 1),
                "specialist": alt_spec["specialist"],
                "specialist_domain": alt_spec["domain"],
                "reason": f"Symptom overlap with Bayesian prior {round(alt['probability']*100, 1)}%"
            })

    triage = evaluate_risk_triage(
        symptoms=symptoms,
        top_disease=top_disease,
        confidence=confidence,
        qa_answers=qa_answers,
        patient_context=patient_context,
        biomarkers=biomarkers
    )

    # Closed-Loop Adaptive Intelligence Additions
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
        "top_disease": top_disease,
        "confidence_percentage": round(confidence, 1),
        "severity": top_info.get("severity", "Moderate"),
        "specialist_recommended": specialist_res["specialist"],
        "specialist_domain": specialist_res["domain"],
        "specialist_rationale": specialist_res["rationale"],
        "medical_advice": top_info.get("advice", ""),
        "recommended_diagnostic_tests": top_info.get("recommended_tests", ["Complete Blood Count (CBC)"]),
        "triage": triage,
        "xai_reasoning": xai_factors,
        "other_possibilities": alternatives,
        # Closed-loop enhancements
        "entropy_uncertainty": entropy_uncertainty,
        "explainable_decision_map": decision_map,
        "minimum_diagnostic_test_set": min_test_set
    }

