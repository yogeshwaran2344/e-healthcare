"""
Evaluation script for the Disease Prediction Engine.
Tests model behavior across typical symptom combinations.
"""

from .predictor import predict_health_condition, get_symptom_catalog
from .dataset import DISEASES_DB

def run_evaluation():
    print("Testing Disease Prediction Engine across sample cases...\n")
    test_cases = [
        ("Pneumonia", ["high_fever", "productive_cough_phlegm", "breathlessness_shortness_of_breath", "chest_tightness"]),
        ("COVID-19", ["high_fever", "dry_cough", "loss_of_taste_smell", "fatigue"]),
        ("Typhoid Fever", ["high_fever", "abdominal_pain", "severe_headache", "loss_of_appetite"]),
        ("Cardiac Warning", ["sharp_chest_pain", "palpitations_rapid_heartbeat", "sweating", "dizziness_lightheadedness"]),
        ("Gastroenteritis", ["vomiting", "diarrhea", "abdominal_pain", "nausea"])
    ]
    
    for expected, symptoms in test_cases:
        result = predict_health_condition(symptoms)
        print(f"Symptoms: {symptoms}")
        print(f"-> Predicted: {result['top_disease']} ({result['confidence_percentage']}%)")
        print(f"-> Recommended Specialist: {result['specialist_recommended']}")
        print(f"-> Recommended Tests: {result['recommended_diagnostic_tests']}")
        print(f"-> Needs Lab Report Upload: {result['needs_lab_reports']}")
        print("-" * 60)

if __name__ == "__main__":
    run_evaluation()
