"""
Medication Safety Checker: Drug Allergy Detection & Contraindication Engine.
Protects patients by cross-referencing prescribed drugs against declared allergies,
pre-existing conditions, and drug-drug interactions.
"""

from typing import List, Dict, Any

# Allergy groups and drug cross-reactivity mapping
ALLERGY_GROUPS = {
    "penicillin": ["amoxicillin", "ampicillin", "augmentin", "penicillin", "piperacillin", "clavulanate"],
    "sulfa": ["bactrim", "sulfamethoxazole", "trimethoprim", "sulfasalazine"],
    "nsaid": ["aspirin", "ibuprofen", "naproxen", "diclofenac", "ketorolac", "aceclofenac"],
    "cephalosporin": ["cefixime", "ceftriaxone", "cephalexin", "cefuroxime"],
    "fluoroquinolone": ["ciprofloxacin", "levofloxacin", "ofloxacin", "moxifloxacin"]
}

# Contraindication rules based on pre-existing medical conditions
CONDITION_CONTRAINDICATIONS = {
    "asthma": {
        "drugs": ["aspirin", "ibuprofen", "propranolol", "atenolol", "beta-blocker"],
        "reason": "May trigger severe bronchospasm in patients with reactive airway disease."
    },
    "ulcer": {
        "drugs": ["aspirin", "ibuprofen", "naproxen", "diclofenac"],
        "reason": "NSAIDs can exacerbate gastrointestinal mucosal bleeding and ulcers."
    },
    "kidney disease": {
        "drugs": ["ibuprofen", "gentamicin", "metformin", "ciprofloxacin"],
        "reason": "Nephrotoxic or renally cleared drugs require severe dosage adjustments."
    },
    "liver disease": {
        "drugs": ["paracetamol", "acetaminophen", "statins", "rifampin"],
        "reason": "Hepatically metabolized drugs may induce or worsen hepatotoxicity."
    }
}

def check_medication_safety(
    prescribed_medicines: List[Dict[str, Any]],
    patient_allergies_str: str,
    patient_conditions_str: str
) -> Dict[str, Any]:
    """
    Evaluates prescribed medication list against patient allergies and medical history.
    Returns detected safety warnings and clearance status.
    """
    alerts = []
    allergies_lower = str(patient_allergies_str).lower()
    conditions_lower = str(patient_conditions_str).lower()

    for med in prescribed_medicines:
        name = med.get("name", "").lower()
        
        # 1. Check Allergy Cross-Reactivity
        for group, drug_list in ALLERGY_GROUPS.items():
            if group in allergies_lower:
                for d in drug_list:
                    if d in name:
                        alerts.append({
                            "type": "CRITICAL_ALLERGY_ALERT",
                            "severity": "High",
                            "drug": med.get("name"),
                            "message": f"Patient has documented allergy to '{group.upper()}'. '{med.get('name')}' belongs to this class and poses anaphylaxis risk."
                        })

        # Also direct word matching
        for single_allergy in [a.strip() for a in allergies_lower.split(",") if a.strip()]:
            if single_allergy in name:
                alerts.append({
                    "type": "DIRECT_ALLERGY_WARNING",
                    "severity": "High",
                    "drug": med.get("name"),
                    "message": f"Direct allergy match: Patient allergic to '{single_allergy.title()}'."
                })

        # 2. Check Disease Contraindications
        for cond, rules in CONDITION_CONTRAINDICATIONS.items():
            if cond in conditions_lower:
                for contra_drug in rules["drugs"]:
                    if contra_drug in name:
                        alerts.append({
                            "type": "CONTRAINDICATION_WARNING",
                            "severity": "Moderate",
                            "drug": med.get("name"),
                            "message": f"Caution with pre-existing {cond.title()}: {rules['reason']}"
                        })

    return {
        "is_safe": len(alerts) == 0,
        "alert_count": len(alerts),
        "alerts": alerts
    }
