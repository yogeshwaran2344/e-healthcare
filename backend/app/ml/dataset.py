"""
Medical Knowledge Base & Disease-Symptom Dataset for E-Healthcare.
Includes symptom profiles, disease metadata, recommended diagnostic tests,
and required specialist doctors.
"""

ALL_SYMPTOMS = [
    # General / Systemic
    "high_fever", "mild_fever", "chills", "fatigue", "general_weakness",
    "loss_of_appetite", "unexplained_weight_loss", "sweating",
    
    # Respiratory
    "dry_cough", "productive_cough_phlegm", "breathlessness_shortness_of_breath",
    "chest_tightness", "sore_throat", "runny_nose", "sneezing", "wheezing",
    
    # Digestive / Abdominal
    "nausea", "vomiting", "abdominal_pain", "diarrhea", "acidity_heartburn",
    "loss_of_taste_smell", "yellowing_of_eyes_skin_jaundice", "dark_urine",
    
    # Cardiovascular
    "sharp_chest_pain", "palpitations_rapid_heartbeat", "swelling_in_legs_ankles",
    "dizziness_lightheadedness",
    
    # Neurological / Musculoskeletal
    "severe_headache", "body_muscle_aches", "joint_pain_swelling", "stiff_neck",
    
    # Dermatological
    "skin_rash", "itching_pruritus", "skin_redness", "blisters"
]

DISEASES_DB = {
    "Pneumonia": {
        "symptoms": ["high_fever", "productive_cough_phlegm", "breathlessness_shortness_of_breath", "chest_tightness", "fatigue", "chills"],
        "specialist": "Pulmonologist",
        "recommended_tests": ["Chest X-Ray", "Complete Blood Count (CBC)", "Sputum Culture"],
        "severity": "Moderate to High",
        "advice": "Rest strictly, stay hydrated, avoid exposure to cold air, and seek medical attention promptly."
    },
    "COVID-19 / Severe Viral Infection": {
        "symptoms": ["high_fever", "dry_cough", "loss_of_taste_smell", "breathlessness_shortness_of_breath", "body_muscle_aches", "fatigue"],
        "specialist": "Pulmonologist / General Physician",
        "recommended_tests": ["RT-PCR Swab Test", "Chest CT Scan", "Complete Blood Count (CBC)"],
        "severity": "High",
        "advice": "Isolate immediately, monitor SpO2 with a pulse oximeter, and consult a doctor immediately if breathing worsens."
    },
    "Common Cold / Upper Respiratory Infection": {
        "symptoms": ["runny_nose", "sneezing", "sore_throat", "mild_fever", "dry_cough", "fatigue"],
        "specialist": "General Physician",
        "recommended_tests": ["Routine Blood Test (if fever persists > 4 days)"],
        "severity": "Low",
        "advice": "Steam inhalation, warm saline gargles, warm fluids, and adequate rest."
    },
    "Bronchitis": {
        "symptoms": ["productive_cough_phlegm", "wheezing", "chest_tightness", "fatigue", "mild_fever"],
        "specialist": "Pulmonologist",
        "recommended_tests": ["Chest X-Ray", "Pulmonary Function Test (Spirometry)"],
        "severity": "Moderate",
        "advice": "Avoid smoke, dust, and cold fluids. Use prescribed inhalers/bronchodilators if recommended."
    },
    "Typhoid Fever": {
        "symptoms": ["high_fever", "abdominal_pain", "severe_headache", "fatigue", "loss_of_appetite", "general_weakness"],
        "specialist": "General Physician",
        "recommended_tests": ["Widal Blood Test", "Typhidot Blood Test", "Complete Blood Count (CBC)"],
        "severity": "Moderate to High",
        "advice": "Drink boiled or filtered water, eat bland cooked food, and do not self-medicate with antibiotics without prescription."
    },
    "Malaria / Dengue": {
        "symptoms": ["high_fever", "chills", "severe_headache", "body_muscle_aches", "nausea", "vomiting", "sweating"],
        "specialist": "General Physician / Infectious Disease",
        "recommended_tests": ["Malaria Antigen Blood Smear", "Dengue NS1 Antigen & Platelet Count Blood Test"],
        "severity": "High",
        "advice": "Maintain high fluid intake (ORS, coconut water), monitor platelet counts, and consult a doctor immediately."
    },
    "Acute Gastroenteritis / Food Poisoning": {
        "symptoms": ["vomiting", "diarrhea", "abdominal_pain", "nausea", "mild_fever", "general_weakness"],
        "specialist": "Gastroenterologist / General Physician",
        "recommended_tests": ["Stool Examination", "Electrolyte Blood Panel", "Abdominal Ultrasound"],
        "severity": "Moderate",
        "advice": "Continuous oral rehydration therapy (ORS), avoid dairy and greasy food, seek urgent help if vomiting prevents hydration."
    },
    "Gastroesophageal Reflux Disease (GERD)": {
        "symptoms": ["acidity_heartburn", "chest_tightness", "nausea", "loss_of_appetite"],
        "specialist": "Gastroenterologist",
        "recommended_tests": ["Upper GI Endoscopy", "Barium Swallow X-Ray"],
        "severity": "Low to Moderate",
        "advice": "Eat small frequent meals, avoid spicy/acidic foods, and do not lie down immediately after eating."
    },
    "Hepatitis / Jaundice": {
        "symptoms": ["yellowing_of_eyes_skin_jaundice", "dark_urine", "abdominal_pain", "loss_of_appetite", "nausea", "fatigue"],
        "specialist": "Hepatologist / Gastroenterologist",
        "recommended_tests": ["Liver Function Test (LFT)", "Total Bilirubin Blood Test", "Abdominal Ultrasound"],
        "severity": "Moderate to High",
        "advice": "Strict low-fat diet, completely avoid alcohol, get liver panel tests done, and consult a specialist."
    },
    "Coronary Artery Disease / Angina (Cardiac Warning)": {
        "symptoms": ["sharp_chest_pain", "chest_tightness", "breathlessness_shortness_of_breath", "palpitations_rapid_heartbeat", "sweating", "dizziness_lightheadedness"],
        "specialist": "Cardiologist",
        "recommended_tests": ["Electrocardiogram (ECG)", "Cardiac Troponin Blood Test", "Echocardiogram", "Chest CT Angiography"],
        "severity": "Critical / Emergency",
        "advice": "IMMEDIATE EMERGENCY: Go to the nearest emergency room or hospital. Rest completely and avoid exertion."
    },
    "Hypertension / Cardiovascular Stress": {
        "symptoms": ["severe_headache", "dizziness_lightheadedness", "palpitations_rapid_heartbeat", "fatigue", "swelling_in_legs_ankles"],
        "specialist": "Cardiologist / Physician",
        "recommended_tests": ["24-Hour BP Monitoring", "Lipid Profile Blood Test", "Kidney Function Test (KFT)", "ECG"],
        "severity": "Moderate",
        "advice": "Limit sodium intake, avoid stress and caffeine, check blood pressure twice daily, and consult your doctor."
    },
    "Migraine / Tension Headache": {
        "symptoms": ["severe_headache", "nausea", "dizziness_lightheadedness", "fatigue"],
        "specialist": "Neurologist",
        "recommended_tests": ["Brain MRI / CT Scan (to rule out secondary causes if recurrent)"],
        "severity": "Moderate",
        "advice": "Rest in a quiet, dark room, hydrate well, avoid trigger foods, and track headache frequency."
    },
    "Rheumatoid Arthritis / Joint Inflammation": {
        "symptoms": ["joint_pain_swelling", "body_muscle_aches", "fatigue", "general_weakness"],
        "specialist": "Rheumatologist / Orthopedic",
        "recommended_tests": ["Rheumatoid Factor (RF) Blood Test", "Joint X-Ray", "Anti-CCP Blood Test", "ESR / CRP"],
        "severity": "Moderate",
        "advice": "Gentle range-of-motion exercises, warm compresses on affected joints, and consult a rheumatologist."
    },
    "Allergic Dermatitis / Eczema": {
        "symptoms": ["skin_rash", "itching_pruritus", "skin_redness", "blisters"],
        "specialist": "Dermatologist",
        "recommended_tests": ["Skin Allergy Patch Test", "Serum IgE Blood Test"],
        "severity": "Low to Moderate",
        "advice": "Apply fragrance-free moisturizers, avoid scratching, avoid allergens and harsh soaps."
    }
}
