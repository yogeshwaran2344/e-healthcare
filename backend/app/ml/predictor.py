"""
Intelligent Disease Prediction & Diagnostic Test Recommendation Engine.
Built using Bayesian probabilistic modeling & medical data mining principles.
Pure Python/Numpy implementation to ensure 100% platform portability and zero DLL dependency issues.
"""

import math
from .dataset import ALL_SYMPTOMS, DISEASES_DB

class DiseasePredictionEngine:
    def __init__(self):
        self.all_symptoms = ALL_SYMPTOMS
        self.diseases = DISEASES_DB
        self.symptom_set = set(ALL_SYMPTOMS)
        
        # Hyperparameters for Bayesian inference
        self.p_core_present = 0.92      # P(symptom=1 | disease has this symptom)
        self.p_core_absent = 0.08       # P(symptom=0 | disease has this symptom)
        self.p_noncore_present = 0.03   # P(symptom=1 | disease does NOT have this symptom)
        self.p_noncore_absent = 0.97    # P(symptom=0 | disease does NOT have this symptom)

    def predict(self, input_symptoms: list[str]) -> dict:
        """
        Calculates posterior probability distribution over all diseases given the selected symptoms,
        computes confidence scores, and determines recommended diagnostic lab tests.
        """
        valid_symptoms = [s for s in input_symptoms if s in self.symptom_set]
        
        if not valid_symptoms:
            return {
                "error": "No valid symptoms provided.",
                "top_disease": None,
                "confidence_percentage": 0.0,
                "other_possibilities": [],
                "recommended_diagnostic_tests": [],
                "needs_lab_reports": False
            }

        input_set = set(valid_symptoms)
        num_diseases = len(self.diseases)
        prior = 1.0 / num_diseases
        log_prior = math.log(prior)

        disease_scores = []

        for disease_name, info in self.diseases.items():
            disease_symptoms = set(info["symptoms"])
            
            # 1. Bayesian Log-Likelihood
            log_likelihood = 0.0
            for s in self.all_symptoms:
                is_selected = s in input_set
                is_core = s in disease_symptoms
                
                if is_selected:
                    p = self.p_core_present if is_core else self.p_noncore_present
                else:
                    p = self.p_core_absent if is_core else self.p_noncore_absent
                log_likelihood += math.log(max(p, 1e-9))
                
            log_posterior = log_prior + log_likelihood

            # 2. Overlap / Jaccard similarity between patient symptoms and disease symptoms
            intersection = len(input_set & disease_symptoms)
            union = len(input_set | disease_symptoms)
            jaccard = intersection / union if union > 0 else 0.0
            
            # Recall: what proportion of patient's symptoms match this disease
            patient_match_ratio = intersection / len(input_set) if len(input_set) > 0 else 0.0

            disease_scores.append({
                "disease": disease_name,
                "log_post": log_posterior,
                "jaccard": jaccard,
                "match_ratio": patient_match_ratio,
                "info": info
            })

        # Softmax normalization of Bayesian log-posteriors
        max_log = max(d["log_post"] for d in disease_scores)
        sum_exp = sum(math.exp(d["log_post"] - max_log) for d in disease_scores)
        
        for d in disease_scores:
            bayes_prob = math.exp(d["log_post"] - max_log) / sum_exp
            # Blend Bayesian posterior with direct symptom match ratio for human-realistic confidence
            blended_confidence = (bayes_prob * 0.65) + (d["match_ratio"] * 0.35)
            d["prob"] = round(blended_confidence * 100, 1)

        # Sort by final score
        disease_scores.sort(key=lambda x: (x["prob"], x["jaccard"]), reverse=True)
        top = disease_scores[0]
        top_disease_name = top["disease"]
        top_info = top["info"]
        confidence = min(max(top["prob"], 20.0), 96.5)

        # Build list of alternative possibilities
        alternatives = []
        for alt in disease_scores[1:4]:
            if alt["prob"] > 10.0:
                alternatives.append({
                    "disease": alt["disease"],
                    "confidence_percentage": alt["prob"],
                    "specialist": alt["info"].get("specialist", "General Physician")
                })

        # Diagnostic test recommendation criteria:
        # As per project requirements: If system cannot be fully conclusive (< 82%)
        # or if condition has moderate-to-high severity, suggest tests and urge report upload.
        is_high_severity = top_info.get("severity") in ["High", "Critical / Emergency", "Moderate to High"]
        needs_lab_reports = confidence < 82.0 or is_high_severity

        return {
            "top_disease": top_disease_name,
            "confidence_percentage": round(confidence, 1),
            "severity": top_info.get("severity", "Moderate"),
            "specialist_recommended": top_info.get("specialist", "General Physician"),
            "medical_advice": top_info.get("advice", ""),
            "recommended_diagnostic_tests": top_info.get("recommended_tests", ["Complete Blood Count (CBC)"]),
            "needs_lab_reports": needs_lab_reports,
            "report_instructions": (
                f"We strongly recommend undergoing: {', '.join(top_info.get('recommended_tests', ['diagnostic lab test']))}. "
                f"Please upload an image of your test report/scan in the consultation portal for doctor verification and prescription."
                if needs_lab_reports else "Symptoms match closely. Consult with a doctor for confirmation and safe prescription."
            ),
            "other_possibilities": alternatives
        }

# Global singleton
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = DiseasePredictionEngine()
    return _engine

def predict_health_condition(selected_symptoms: list[str]) -> dict:
    return get_engine().predict(selected_symptoms)

def get_symptom_catalog():
    """Return all available symptoms formatted for UI presentation."""
    catalog = []
    for s in ALL_SYMPTOMS:
        label = s.replace("_", " ").title()
        catalog.append({"key": s, "label": label})
    return catalog
