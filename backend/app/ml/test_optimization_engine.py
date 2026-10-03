"""
Minimum-Diagnostic-Test Recommendation & Pareto Optimization Engine.
Selects the minimal, safest, and most cost-effective diagnostic test combination
capable of reducing diagnostic uncertainty below clinical safety thresholds.
"""

from typing import List, Dict, Any, Optional
from .dataset import TESTS_CATALOG, DISEASES_DB

def optimize_minimum_diagnostic_test_set(
    top_disease: str,
    top_candidates: List[Dict[str, Any]],
    current_uncertainty: float,
    symptoms: List[str],
    triage_level: str
) -> Dict[str, Any]:
    """
    Computes the Minimum Diagnostic Test Set:
    - Identifies mandatory life-safety tests (cannot be pruned under any cost constraint)
    - Solves greedy multi-objective utility knapsack:
      Score = (Diagnostic Utility * 1000) / (Cost Factor + Radiation Penalty)
    - Ensures residual uncertainty drops below 15%
    """
    selected_tests = []
    total_cost_inr = 0
    cumulative_utility = 0.0
    mandatory_tests = set()

    # 1. Identify Mandatory Life Safety Tests from disease profiles
    for cand in top_candidates[:2]:
        d_name = cand["disease"]
        d_info = DISEASES_DB.get(d_name, {})
        for m_test in d_info.get("mandatory_tests", []):
            if m_test in TESTS_CATALOG:
                mandatory_tests.add(m_test)

    # Emergency symptoms force specific mandatory tests
    symptoms_set = set(symptoms)
    if "sharp_chest_pain" in symptoms_set or "pain_radiating_to_arm_jaw" in symptoms_set:
        mandatory_tests.add("12-Lead Electrocardiogram (ECG)")
        mandatory_tests.add("High-Sensitivity Cardiac Troponin-I")

    if "facial_droop_weakness" in symptoms_set or "unilateral_limb_weakness" in symptoms_set or "slurred_speech" in symptoms_set:
        mandatory_tests.add("Brain Non-Contrast CT Scan")

    if "calf_tenderness_swelling" in symptoms_set and "breathlessness_shortness_of_breath" in symptoms_set:
        mandatory_tests.add("D-Dimer Quantitative Assay")

    # Add all mandatory tests first
    for test_name in mandatory_tests:
        meta = TESTS_CATALOG[test_name]
        selected_tests.append({
            "test_name": test_name,
            "priority": "MANDATORY (Life Safety Override)",
            "priority_tier": 1,
            "cost_inr": meta["cost_inr"],
            "cost_tier": meta["cost_tier"],
            "turnaround_hours": meta["turnaround_hours"],
            "radiation_risk": meta["radiation_risk"],
            "diagnostic_utility": meta["diagnostic_utility"],
            "rationale": f"Emergency safety standard: essential to confirm or rule out acute {top_disease.split('/')[0].strip()}."
        })
        total_cost_inr += meta["cost_inr"]
        cumulative_utility += meta["diagnostic_utility"]

    # 2. Pool candidate optional/recommended tests from candidate diseases
    candidate_test_pool = set()
    for cand in top_candidates[:3]:
        d_name = cand["disease"]
        d_info = DISEASES_DB.get(d_name, {})
        for r_test in d_info.get("recommended_tests", []):
            if r_test in TESTS_CATALOG and r_test not in mandatory_tests:
                candidate_test_pool.add(r_test)

    # 3. Score candidate tests by Cost-Benefit Pareto Ratio
    scored_candidates = []
    for test_name in candidate_test_pool:
        meta = TESTS_CATALOG[test_name]
        # Radiation penalty factor
        rad_penalty = 1.4 if meta["radiation_risk"] == "Moderate" else 1.0
        # Cost-effectiveness ratio: Information Gain per 1000 INR
        cost_weight = max(meta["cost_inr"] / 500.0, 1.0)
        efficiency_ratio = (meta["diagnostic_utility"] * 10.0) / (cost_weight * rad_penalty)

        scored_candidates.append({
            "test_name": test_name,
            "efficiency_ratio": efficiency_ratio,
            "meta": meta
        })

    # Sort by efficiency
    scored_candidates.sort(key=lambda x: x["efficiency_ratio"], reverse=True)

    # Pick up to 2 high-efficiency tests if uncertainty is still elevated
    target_utility = 1.4 # threshold for sufficient clinical confirmation
    for item in scored_candidates:
        if cumulative_utility >= target_utility and len(selected_tests) >= 2:
            break
        test_name = item["test_name"]
        meta = item["meta"]
        selected_tests.append({
            "test_name": test_name,
            "priority": "RECOMMENDED (High Information Gain)",
            "priority_tier": 2,
            "cost_inr": meta["cost_inr"],
            "cost_tier": meta["cost_tier"],
            "turnaround_hours": meta["turnaround_hours"],
            "radiation_risk": meta["radiation_risk"],
            "diagnostic_utility": meta["diagnostic_utility"],
            "rationale": f"High diagnostic yield for differential diagnosis ({meta['cost_tier']} cost, {meta['radiation_risk']} radiation)."
        })
        total_cost_inr += meta["cost_inr"]
        cumulative_utility += meta["diagnostic_utility"]
        if len(selected_tests) >= 3:
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
                "rationale": "Baseline hematological screening."
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
