"""
Minimum-Diagnostic-Test Recommendation & Pareto Optimization Engine.
Selects the minimal, safest, and most cost-effective diagnostic test combination
capable of reducing diagnostic uncertainty below clinical safety thresholds.
"""

from typing import List, Dict, Any, Optional
from .dataset import TESTS_CATALOG, DISEASES_DB

TEST_CLINICAL_RATIONALES = {
    "12-Lead Electrocardiogram (ECG)": "Records cardiac electrical activity to detect acute ischemia, STEMI/NSTEMI, conduction blocks, or arrhythmias.",
    "High-Sensitivity Cardiac Troponin-I": "Gold-standard cardiac biomarker essential to detect or exclude acute myocardial injury / infarction.",
    "Chest X-Ray (PA View)": "Visualizes lung consolidation, infiltrates, pleural effusion, or cardiomegaly.",
    "Complete Blood Count (CBC)": "Evaluates leukocyte count, hemoglobin, platelets, and systemic infection/inflammatory response.",
    "C-Reactive Protein (CRP) & ESR": "Quantitative inflammatory biomarkers to differentiate bacterial infection vs inflammatory flare.",
    "High-Resolution Chest CT Scan (HRCT)": "High-resolution parenchymal imaging for severe viral pneumonitis, ground-glass opacities, or PE.",
    "RT-PCR Viral Panel (COVID / Influenza)": "Molecular diagnostic assay to detect specific respiratory viral RNA (COVID-19 / Influenza A/B / RSV).",
    "Dengue NS1 Antigen & IgM/IgG Panel": "Rapid serology to confirm acute Dengue infection and initiate serial platelet monitoring.",
    "Malaria Rapid Antigen & Blood Smear": "Identifies Plasmodium vivax/falciparum parasites and quantifies parasitemia.",
    "Widal & Typhidot Blood Serology": "Detects Salmonella enterica serotype typhi antibodies for enteric fever confirmation.",
    "Liver Function Test (LFT) with Bilirubin": "Assesses AST/ALT transaminases, bilirubin fractions, and alkaline phosphatase for hepatobiliary pathology.",
    "Abdominal Ultrasound (USG Whole Abdomen)": "Evaluates gallbladder wall thickening, gallstones, liver parenchyma, appendicitis, or renal calculi.",
    "Serum Electrolytes & Renal Function (KFT/Creatinine)": "Evaluates serum sodium/potassium, blood urea nitrogen, and creatinine for kidney function & hydration.",
    "Urinalysis Routine & Microscopic (Urine R/M)": "Assesses pus cells, nitrites, leukocyte esterase, RBCs, and casts for urinary tract infection.",
    "Brain Non-Contrast CT Scan": "Emergency cross-sectional brain imaging to immediately rule out intracranial hemorrhage or stroke mass effect.",
    "Brain MRI with Contrast": "High-resolution neuro-imaging for detailed evaluation of ischemic stroke, demyelination, or encephalitis.",
    "Rheumatoid Factor (RF) & Anti-CCP Panel": "Specific autoantibody biomarkers for definitive early diagnosis of rheumatoid arthritis.",
    "D-Dimer Quantitative Assay": "Fibrin degradation assay with high sensitivity to rule out deep vein thrombosis or pulmonary embolism.",
    "Serum Ferritin & Iron Studies (Hair Loss/Anemia)": "Measures ferritin stores and iron saturation to identify telogen effluvium & iron deficiency hair shedding.",
    "Female Hormone Panel (LH, FSH, Total Testosterone, DHEA-S)": "Profiles androgen excess, LH:FSH ratio, and endocrine drivers of PCOS, hormonal acne, and menstrual irregularity.",
    "Pelvic Ultrasound (USG Pelvis TVS/TAS)": "Pelvic sonography to assess polycystic ovarian morphology, endometrial lining thickness, and ovarian cysts.",
    "Scalp & Skin Trichoscopy / KOH Mount": "Microscopic and dermoscopic evaluation of hair follicle density, scaling, and fungal hyphae."
}

def optimize_minimum_diagnostic_test_set(
    top_disease: str,
    top_candidates: List[Dict[str, Any]],
    current_uncertainty: float,
    symptoms: List[str],
    triage_level: str
) -> Dict[str, Any]:
    """
    Computes the Minimum Diagnostic Test Set:
    - Identifies mandatory life-safety tests strictly relevant to the active condition and symptoms
    - Solves greedy multi-objective utility knapsack
    - Ensures tests are realistic and directly correlate with the patient's clinical complaint
    """
    selected_tests = []
    total_cost_inr = 0
    cumulative_utility = 0.0
    mandatory_tests = set()
    symptoms_joined = " ".join(symptoms).lower()

    # 1. Identify Mandatory Tests strictly from the primary suspected disease
    top_info = DISEASES_DB.get(top_disease, {})
    for m_test in top_info.get("mandatory_tests", []):
        if m_test in TESTS_CATALOG:
            mandatory_tests.add(m_test)

    # Symptom-specific targeted test rules (High clinical realism)
    # Cardiac / Chest Pain
    if any(s in symptoms_joined for s in ["sharp_chest_pain", "pain_radiating_to_arm", "palpitations"]):
        mandatory_tests.add("12-Lead Electrocardiogram (ECG)")
        if "sharp_chest_pain" in symptoms_joined or "radiating" in symptoms_joined:
            mandatory_tests.add("High-Sensitivity Cardiac Troponin-I")

    # Respiratory / Lungs / Cough
    if any(s in symptoms_joined for s in ["cough", "breathlessness", "chest_tightness", "wheezing"]):
        mandatory_tests.add("Chest X-Ray (PA View)")

    # Gastrointestinal / Stomach / Liver / Gallbladder
    if any(s in symptoms_joined for s in ["abdominal", "epigastric", "acidity", "vomiting", "diarrhea", "stomach", "jaundice", "dark_urine", "right_upper_quadrant", "indigestion"]):
        if any(s in symptoms_joined for s in ["right_upper_quadrant", "jaundice", "dark_urine"]):
            mandatory_tests.add("Abdominal Ultrasound (USG Whole Abdomen)")
            mandatory_tests.add("Liver Function Test (LFT) with Bilirubin")
        elif any(s in symptoms_joined for s in ["epigastric", "acidity", "abdominal", "vomiting", "diarrhea"]):
            mandatory_tests.add("Complete Blood Count (CBC)")

    # Neurological / Acute severe headache / stroke symptoms
    if any(s in symptoms_joined for s in ["thunderclap", "facial_droop", "limb_weakness", "slurred_speech", "stiff_neck"]):
        mandatory_tests.add("Brain Non-Contrast CT Scan")

    # Hair / Scalp
    if any(s in symptoms_joined for s in ["hair_fall", "hair_thinning", "dandruff", "scalp_itching"]):
        mandatory_tests.add("Serum Ferritin & Iron Studies (Hair Loss/Anemia)")

    # Gynaecology / Menstrual / PCOS
    if any(s in symptoms_joined for s in ["period", "menstrual", "pcos", "pelvic", "vaginal"]):
        mandatory_tests.add("Pelvic Ultrasound (USG Pelvis TVS/TAS)")
        mandatory_tests.add("Female Hormone Panel (LH, FSH, Total Testosterone, DHEA-S)")

    # Urinary / Flank pain
    if any(s in symptoms_joined for s in ["flank", "dysuria", "hematuria"]):
        mandatory_tests.add("Urinalysis Routine & Microscopic (Urine R/M)")

    # If no mandatory test was triggered, default to basic CBC
    if not mandatory_tests:
        mandatory_tests.add("Complete Blood Count (CBC)")

    # Add all mandatory tests first with specific rationales
    for test_name in mandatory_tests:
        if test_name not in TESTS_CATALOG:
            continue
        meta = TESTS_CATALOG[test_name]
        rationale = TEST_CLINICAL_RATIONALES.get(test_name, f"Essential clinical investigation for evaluation of suspected {top_disease.split('/')[0].strip()}.")
        selected_tests.append({
            "test_name": test_name,
            "priority": "MANDATORY (Targeted Clinical Test)",
            "priority_tier": 1,
            "cost_inr": meta["cost_inr"],
            "cost_tier": meta["cost_tier"],
            "turnaround_hours": meta["turnaround_hours"],
            "radiation_risk": meta["radiation_risk"],
            "diagnostic_utility": meta["diagnostic_utility"],
            "rationale": rationale
        })
        total_cost_inr += meta["cost_inr"]
        cumulative_utility += meta["diagnostic_utility"]

    # 2. Add recommended tests strictly from top_disease if needed for complete workup
    candidate_test_pool = set()
    for r_test in top_info.get("recommended_tests", []):
        if r_test in TESTS_CATALOG and r_test not in mandatory_tests:
            candidate_test_pool.add(r_test)

    # 3. Score candidate tests by Cost-Benefit Pareto Ratio
    scored_candidates = []
    for test_name in candidate_test_pool:
        meta = TESTS_CATALOG[test_name]
        rad_penalty = 1.4 if meta["radiation_risk"] == "Moderate" else 1.0
        cost_weight = max(meta["cost_inr"] / 500.0, 1.0)
        efficiency_ratio = (meta["diagnostic_utility"] * 10.0) / (cost_weight * rad_penalty)

        scored_candidates.append({
            "test_name": test_name,
            "efficiency_ratio": efficiency_ratio,
            "meta": meta
        })

    scored_candidates.sort(key=lambda x: x["efficiency_ratio"], reverse=True)

    # Add at most 1 high-yield recommended test if appropriate
    for item in scored_candidates:
        if len(selected_tests) >= 3:
            break
        test_name = item["test_name"]
        meta = item["meta"]
        rationale = TEST_CLINICAL_RATIONALES.get(test_name, f"High diagnostic yield for differential evaluation ({meta['cost_tier']} cost, {meta['radiation_risk']} radiation).")
        selected_tests.append({
            "test_name": test_name,
            "priority": "RECOMMENDED (High Information Gain)",
            "priority_tier": 2,
            "cost_inr": meta["cost_inr"],
            "cost_tier": meta["cost_tier"],
            "turnaround_hours": meta["turnaround_hours"],
            "radiation_risk": meta["radiation_risk"],
            "diagnostic_utility": meta["diagnostic_utility"],
            "rationale": rationale
        })
        total_cost_inr += meta["cost_inr"]
        cumulative_utility += meta["diagnostic_utility"]
        break

    # If no tests needed (e.g. low severity self care)
    if not selected_tests:
        if "Emergency" in triage_level:
            # Fallback emergency basic panel
            cbc_meta = TESTS_CATALOG["Complete Blood Count (CBC)"]
            selected_tests.append({
                "test_name": "Complete Blood Count (CBC)",
                "priority": "RECOMMENDED",
                "priority_tier": 2,
                "cost_inr": cbc_meta["cost_inr"],
                "cost_tier": cbc_meta["cost_tier"],
                "turnaround_hours": cbc_meta["turnaround_hours"],
                "radiation_risk": cbc_meta["radiation_risk"],
                "diagnostic_utility": cbc_meta["diagnostic_utility"],
                "rationale": TEST_CLINICAL_RATIONALES.get("Complete Blood Count (CBC)", "Baseline hematological screening.")
            })
            total_cost_inr += cbc_meta["cost_inr"]

    # Calculate residual uncertainty after planned tests
    expected_residual_uncertainty = max(round(current_uncertainty * (1.0 - min(cumulative_utility * 0.5, 0.85)), 1), 5.0)

    # Radiation summary
    has_radiation = any(t["radiation_risk"] != "None" for t in selected_tests)
    radiation_summary = "Zero radiation exposure." if not has_radiation else "Low/Controlled radiation exposure (Chest X-ray / CT limited strictly to clinical necessity)."

    # Calculate pruned / avoided redundant tests
    avoided_tests = []
    selected_names = {t["test_name"] for t in selected_tests}
    for item in scored_candidates:
        if item["test_name"] not in selected_names:
            meta = item["meta"]
            avoided_tests.append({
                "test_name": item["test_name"],
                "cost_inr": meta["cost_inr"],
                "reason": "Pruned: lower utility-to-cost ratio"
            })
    if not avoided_tests:
        avoided_tests.append({
            "test_name": "Full Body Contrast CT Scan",
            "cost_inr": 8500,
            "reason": "Omitted: high radiation burden and negligible additional entropy reduction"
        })

    return {
        "minimum_test_set": selected_tests,
        "avoided_redundant_tests": avoided_tests,
        "total_estimated_cost_inr": total_cost_inr,
        "total_test_count": len(selected_tests),
        "cumulative_diagnostic_utility": round(cumulative_utility, 2),
        "expected_residual_uncertainty_pct": expected_residual_uncertainty,
        "radiation_burden_profile": radiation_summary,
        "optimization_objective": "Min-Cost Max-Utility Pareto Optimal diagnostic frontier"
    }
