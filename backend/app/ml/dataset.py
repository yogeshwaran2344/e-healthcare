"""
Medical Knowledge Base & Disease-Symptom Dataset for E-Healthcare.
Includes expanded 75+ categorized symptoms, disease metadata, diagnostic tests catalog
with cost/information-gain/radiation-risk metadata, and clinical decision parameters.
"""

# Categorized symptom definitions for rich multi-system selection
SYMPTOMS_BY_CATEGORY = {
    "Respiratory": [
        {"id": "dry_cough", "label": "Dry Cough (Non-productive)"},
        {"id": "productive_cough_phlegm", "label": "Productive Cough with Phlegm/Sputum"},
        {"id": "breathlessness_shortness_of_breath", "label": "Shortness of Breath / Dyspnea"},
        {"id": "chest_tightness", "label": "Chest Tightness / Constriction"},
        {"id": "wheezing", "label": "Wheezing / Whistling Breath"},
        {"id": "sore_throat", "label": "Sore Throat / Pharyngitis"},
        {"id": "runny_nose", "label": "Runny / Congested Nose (Rhinorrhea)"},
        {"id": "sneezing", "label": "Frequent Sneezing"},
        {"id": "hemoptysis_coughing_blood", "label": "Coughing Blood (Hemoptysis)"},
        {"id": "stridor_noisy_breathing", "label": "Stridor / High-Pitched Breathing Sound"}
    ],
    "Cardiovascular": [
        {"id": "sharp_chest_pain", "label": "Sharp / Crushing Chest Pain (Retrosternal)"},
        {"id": "palpitations_rapid_heartbeat", "label": "Palpitations / Rapid Racing Heartbeat"},
        {"id": "pain_radiating_to_arm_jaw", "label": "Pain Radiating to Left Arm, Neck or Jaw"},
        {"id": "swelling_in_legs_ankles", "label": "Peripheral Edema (Swollen Ankles/Legs)"},
        {"id": "dizziness_lightheadedness", "label": "Dizziness / Lightheadedness / Presyncope"},
        {"id": "syncope_fainting", "label": "Syncope / Sudden Blackout or Fainting"},
        {"id": "cold_clammy_sweats", "label": "Cold Clammy Sweating (Diaphoresis)"},
        {"id": "orthopnea_lying_flat_breathless", "label": "Orthopnea (Breathless when lying flat)"}
    ],
    "Gastrointestinal & Hepatic": [
        {"id": "nausea", "label": "Nausea / Sensation of Vomiting"},
        {"id": "vomiting", "label": "Active Vomiting / Emesis"},
        {"id": "abdominal_pain", "label": "Generalized Abdominal Pain / Cramps"},
        {"id": "epigastric_burning_pain", "label": "Epigastric / Burning Stomach Pain"},
        {"id": "right_upper_quadrant_pain", "label": "Right Upper Quadrant Rib Pain"},
        {"id": "diarrhea", "label": "Watery Diarrhea / Loose Stools"},
        {"id": "acidity_heartburn", "label": "Acid Reflux / Heartburn / GERD"},
        {"id": "loss_of_appetite", "label": "Loss of Appetite (Anorexia)"},
        {"id": "yellowing_of_eyes_skin_jaundice", "label": "Yellowing of Sclera/Skin (Jaundice)"},
        {"id": "dark_urine", "label": "Dark Cola-Colored Urine"},
        {"id": "pale_clay_colored_stools", "label": "Pale / Clay-Colored Stools"},
        {"id": "hematemesis_blood_in_vomit", "label": "Blood in Vomit (Hematemesis)"},
        {"id": "bloating_abdominal_distension", "label": "Abdominal Bloating & Gas Distension"}
    ],
    "Neurological & Sensory": [
        {"id": "severe_headache", "label": "Severe Throbbing Headache"},
        {"id": "sudden_thunderclap_headache", "label": "Sudden Thunderclap 'Worst Headache of Life'"},
        {"id": "stiff_neck", "label": "Stiff Neck (Nuchal Rigidity)"},
        {"id": "loss_of_taste_smell", "label": "Loss of Taste or Smell (Anosmia/Ageusia)"},
        {"id": "facial_droop_weakness", "label": "Unilateral Facial Droop / Weakness"},
        {"id": "unilateral_limb_weakness", "label": "One-sided Arm/Leg Weakness or Numbness"},
        {"id": "slurred_speech", "label": "Slurred or Garbled Speech (Dysarthria)"},
        {"id": "photophobia_light_sensitivity", "label": "Photophobia / Sensitivity to Light"},
        {"id": "vertigo_room_spinning", "label": "Vertigo / Sensation of Room Spinning"},
        {"id": "confusion_disorientation", "label": "Acute Confusion / Disorientation"},
        {"id": "tremors_shaking_hands", "label": "Involuntary Hand Shaking / Tremors"}
    ],
    "Systemic & Infectious": [
        {"id": "high_fever", "label": "High Fever (>102°F / 38.9°C)"},
        {"id": "mild_fever", "label": "Mild / Low-Grade Fever (99-101°F)"},
        {"id": "chills", "label": "Chills & Shivering Rigors"},
        {"id": "fatigue", "label": "Overwhelming Fatigue / Exhaustion"},
        {"id": "general_weakness", "label": "General Malaise & Weakness"},
        {"id": "unexplained_weight_loss", "label": "Unexplained Significant Weight Loss"},
        {"id": "night_sweats", "label": "Drenching Night Sweats"},
        {"id": "sweating", "label": "Excessive Daytime Sweating"},
        {"id": "swollen_lymph_nodes", "label": "Swollen Lymph Nodes in Neck/Groin"}
    ],
    "Musculoskeletal": [
        {"id": "body_muscle_aches", "label": "Generalized Muscle Aches (Myalgia)"},
        {"id": "joint_pain_swelling", "label": "Joint Pain & Inflammatory Swelling (Arthralgia)"},
        {"id": "morning_joint_stiffness", "label": "Morning Joint Stiffness (>30 mins)"},
        {"id": "lower_back_pain", "label": "Acute or Chronic Lower Back Pain"},
        {"id": "calf_tenderness_swelling", "label": "Unilateral Calf Pain & Redness (DVT risk)"}
    ],
    "Dermatological": [
        {"id": "skin_rash", "label": "Diffuse Skin Rash / Eruption"},
        {"id": "itching_pruritus", "label": "Severe Generalized Itching (Pruritus)"},
        {"id": "skin_redness", "label": "Localized Skin Erythema / Redness"},
        {"id": "blisters", "label": "Fluid-Filled Blisters or Vesicles"},
        {"id": "petechiae_purpura", "label": "Pinpoint Purple Spots under Skin (Petechiae)"},
        {"id": "hives_urticaria", "label": "Raised Itchy Welts / Hives (Urticaria)"}
    ],
    "Renal & Urological": [
        {"id": "dysuria_burning_urination", "label": "Burning Sensation During Urination (Dysuria)"},
        {"id": "urinary_frequency", "label": "Increased Frequency & Urgency of Urination"},
        {"id": "hematuria_blood_in_urine", "label": "Visible Blood in Urine (Hematuria)"},
        {"id": "flank_kidney_angle_pain", "label": "Flank Pain / Costovertebral Angle Tenderness"},
        {"id": "reduced_urine_output", "label": "Oliguria / Markedly Reduced Urine Output"}
    ],
    "Endocrine & Metabolic": [
        {"id": "excessive_thirst_polydipsia", "label": "Excessive Unquenchable Thirst (Polydipsia)"},
        {"id": "frequent_night_urination_polyuria", "label": "Frequent Night Urination (Polyuria)"},
        {"id": "unexplained_weight_gain", "label": "Rapid Unexplained Weight Gain"},
        {"id": "cold_intolerance", "label": "Extreme Cold Intolerance (Hypothyroid)"},
        {"id": "heat_intolerance", "label": "Excessive Heat Sensitivity & Flushing"},
        {"id": "tremulous_jittery_feeling", "label": "Internal Tremulous or Jittery Feeling"}
    ],
    "ENT & Ophthalmic": [
        {"id": "ear_pain_otalgia", "label": "Ear Ache / Deep Ear Pain (Otalgia)"},
        {"id": "tinnitus_ringing_in_ears", "label": "Ringing or Buzzing in Ears (Tinnitus)"},
        {"id": "eye_redness_conjunctivitis", "label": "Bloodshot Eye Redness / Conjunctivitis"},
        {"id": "blurred_vision", "label": "Sudden or Gradual Blurred Vision"},
        {"id": "epistaxis_nosebleed", "label": "Spontaneous Nosebleed (Epistaxis)"}
    ]
}


# Flat list of all 70+ symptom IDs
ALL_SYMPTOMS = []
for _cat, _items in SYMPTOMS_BY_CATEGORY.items():
    for _item in _items:
        if _item["id"] not in ALL_SYMPTOMS:
            ALL_SYMPTOMS.append(_item["id"])

# Diagnostic Test Catalog with utility metadata
TESTS_CATALOG = {
    "Complete Blood Count (CBC)": {
        "cost_inr": 350,
        "cost_tier": "Low",
        "turnaround_hours": 3,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.82,
        "indicates": ["Infection", "Anemia", "Thrombocytopenia", "Leukocytosis"]
    },
    "C-Reactive Protein (CRP) & ESR": {
        "cost_inr": 500,
        "cost_tier": "Low",
        "turnaround_hours": 4,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.75,
        "indicates": ["Systemic Inflammation", "Autoimmune Activity", "Bacterial Sepsis"]
    },
    "Chest X-Ray (PA View)": {
        "cost_inr": 600,
        "cost_tier": "Low",
        "turnaround_hours": 1,
        "radiation_risk": "Low",
        "invasiveness": "None",
        "diagnostic_utility": 0.85,
        "indicates": ["Pneumonia Consolidation", "Pleural Effusion", "Cardiomegaly", "Pneumothorax"]
    },
    "12-Lead Electrocardiogram (ECG)": {
        "cost_inr": 400,
        "cost_tier": "Low",
        "turnaround_hours": 0.5,
        "radiation_risk": "None",
        "invasiveness": "None",
        "diagnostic_utility": 0.95,
        "indicates": ["STEMI / NSTEMI Ischemia", "Arrhythmia", "Heart Block", "Hypertrophy"]
    },
    "High-Sensitivity Cardiac Troponin-I": {
        "cost_inr": 1200,
        "cost_tier": "Medium",
        "turnaround_hours": 1,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.98,
        "indicates": ["Myocardial Infarction", "Acute Coronary Syndrome", "Myocarditis"]
    },
    "High-Resolution Chest CT Scan (HRCT)": {
        "cost_inr": 4500,
        "cost_tier": "High",
        "turnaround_hours": 4,
        "radiation_risk": "Moderate",
        "invasiveness": "None",
        "diagnostic_utility": 0.94,
        "indicates": ["Severe Viral Pneumonia", "Pulmonary Embolism", "Interstitial Lung Disease"]
    },
    "RT-PCR Viral Panel (COVID / Influenza)": {
        "cost_inr": 900,
        "cost_tier": "Medium",
        "turnaround_hours": 8,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.96,
        "indicates": ["COVID-19", "Influenza A/B", "RSV Infection"]
    },
    "Dengue NS1 Antigen & IgM/IgG Panel": {
        "cost_inr": 1100,
        "cost_tier": "Medium",
        "turnaround_hours": 2,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.92,
        "indicates": ["Acute Dengue Hemorrhagic Fever", "Platelet Threat"]
    },
    "Malaria Rapid Antigen & Blood Smear": {
        "cost_inr": 450,
        "cost_tier": "Low",
        "turnaround_hours": 2,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.90,
        "indicates": ["Plasmodium Vivax / Falciparum Parasites"]
    },
    "Widal & Typhidot Blood Serology": {
        "cost_inr": 550,
        "cost_tier": "Low",
        "turnaround_hours": 4,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.78,
        "indicates": ["Salmonella Typhi Enteric Fever"]
    },
    "Liver Function Test (LFT) with Bilirubin": {
        "cost_inr": 750,
        "cost_tier": "Medium",
        "turnaround_hours": 4,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.88,
        "indicates": ["Hepatitis", "Obstructive Jaundice", "Liver Cirrhosis"]
    },
    "Abdominal Ultrasound (USG Whole Abdomen)": {
        "cost_inr": 1800,
        "cost_tier": "Medium",
        "turnaround_hours": 2,
        "radiation_risk": "None",
        "invasiveness": "None",
        "diagnostic_utility": 0.89,
        "indicates": ["Appendicitis", "Cholecystitis Gallstones", "Fatty Liver", "Nephrolithiasis"]
    },
    "Serum Electrolytes & Renal Function (KFT/Creatinine)": {
        "cost_inr": 800,
        "cost_tier": "Medium",
        "turnaround_hours": 3,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.86,
        "indicates": ["Acute Kidney Injury", "Dehydration Imbalance", "Uremia"]
    },
    "Urinalysis Routine & Microscopic (Urine R/M)": {
        "cost_inr": 250,
        "cost_tier": "Low",
        "turnaround_hours": 1.5,
        "radiation_risk": "None",
        "invasiveness": "None",
        "diagnostic_utility": 0.84,
        "indicates": ["Urinary Tract Infection", "Hematuria", "Proteinuria"]
    },
    "Brain Non-Contrast CT Scan": {
        "cost_inr": 3500,
        "cost_tier": "High",
        "turnaround_hours": 2,
        "radiation_risk": "Moderate",
        "invasiveness": "None",
        "diagnostic_utility": 0.96,
        "indicates": ["Intracranial Hemorrhage", "Acute Ischemic Stroke", "Mass Effect"]
    },
    "Brain MRI with Contrast": {
        "cost_inr": 7500,
        "cost_tier": "High",
        "turnaround_hours": 6,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.98,
        "indicates": ["Subacute Stroke", "Encephalitis", "Multiple Sclerosis", "Aneurysm"]
    },
    "Rheumatoid Factor (RF) & Anti-CCP Panel": {
        "cost_inr": 1600,
        "cost_tier": "Medium",
        "turnaround_hours": 8,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.89,
        "indicates": ["Rheumatoid Arthritis", "Connective Tissue Autoimmunity"]
    },
    "D-Dimer Quantitative Assay": {
        "cost_inr": 1400,
        "cost_tier": "Medium",
        "turnaround_hours": 1.5,
        "radiation_risk": "None",
        "invasiveness": "Low",
        "diagnostic_utility": 0.93,
        "indicates": ["Deep Vein Thrombosis", "Pulmonary Embolism", "Coagulopathy"]
    }
}

DISEASES_DB = {
    "Acute Coronary Syndrome / Angina (Cardiac Emergency)": {
        "symptoms": [
            "sharp_chest_pain", "pain_radiating_to_arm_jaw", "breathlessness_shortness_of_breath",
            "palpitations_rapid_heartbeat", "cold_clammy_sweats", "dizziness_lightheadedness"
        ],
        "mandatory_tests": ["12-Lead Electrocardiogram (ECG)", "High-Sensitivity Cardiac Troponin-I"],
        "recommended_tests": ["Complete Blood Count (CBC)", "Chest X-Ray (PA View)"],
        "specialist": "Interventional Cardiologist",
        "severity": "Critical / Emergency",
        "urgency_score": 98,
        "advice": "CRITICAL EMERGENCY: Administer aspirin 300mg chewable immediately if not allergic. Transfer via Cardiac ALS Ambulance to cath lab trauma facility."
    },
    "Acute Ischemic Stroke / Cerebrovascular Attack": {
        "symptoms": [
            "facial_droop_weakness", "unilateral_limb_weakness", "slurred_speech",
            "sudden_thunderclap_headache", "confusion_disorientation", "vertigo_room_spinning"
        ],
        "mandatory_tests": ["Brain Non-Contrast CT Scan"],
        "recommended_tests": ["12-Lead Electrocardiogram (ECG)", "Serum Electrolytes & Renal Function (KFT/Creatinine)"],
        "specialist": "Neurologist / Stroke Specialist",
        "severity": "Critical / Emergency",
        "urgency_score": 99,
        "advice": "CRITICAL EMERGENCY: Time is brain. Window for thrombolysis (IV tPA) is <4.5 hours from onset. Rush to Stroke Center immediately."
    },
    "Bacterial Pneumonia / Lower Respiratory Infection": {
        "symptoms": [
            "high_fever", "productive_cough_phlegm", "breathlessness_shortness_of_breath",
            "chest_tightness", "fatigue", "chills"
        ],
        "mandatory_tests": ["Chest X-Ray (PA View)", "Complete Blood Count (CBC)"],
        "recommended_tests": ["C-Reactive Protein (CRP) & ESR"],
        "specialist": "Pulmonologist",
        "severity": "Moderate to High",
        "urgency_score": 75,
        "advice": "Start empirical antibiotic protocol after blood/sputum sampling, continuous pulse oximetry SpO2 monitoring, and adequate hydration."
    },
    "COVID-19 / Severe Viral Pneumonitis": {
        "symptoms": [
            "high_fever", "dry_cough", "loss_of_taste_smell", "breathlessness_shortness_of_breath",
            "body_muscle_aches", "fatigue", "headache"
        ],
        "mandatory_tests": ["RT-PCR Viral Panel (COVID / Influenza)", "Complete Blood Count (CBC)"],
        "recommended_tests": ["High-Resolution Chest CT Scan (HRCT)", "C-Reactive Protein (CRP) & ESR"],
        "specialist": "Pulmonologist / Infectious Disease",
        "severity": "High",
        "urgency_score": 80,
        "advice": "Isolate patient, monitor 6-minute walk SpO2 desaturation. If SpO2 drops <94%, administer supplemental oxygen and hospitalize."
    },
    "Acute Dengue Infection with Warning Signs": {
        "symptoms": [
            "high_fever", "severe_headache", "body_muscle_aches", "nausea",
            "vomiting", "petechiae_purpura", "abdominal_pain", "chills"
        ],
        "mandatory_tests": ["Dengue NS1 Antigen & IgM/IgG Panel", "Complete Blood Count (CBC)"],
        "recommended_tests": ["Liver Function Test (LFT) with Bilirubin"],
        "specialist": "Infectious Disease / General Physician",
        "severity": "High",
        "urgency_score": 85,
        "advice": "Close hematocrit and serial platelet monitoring every 12 hours. Strict fluid replacement therapy. Avoid NSAIDs (aspirin, ibuprofen) due to bleeding risk."
    },
    "Typhoid Enteric Fever": {
        "symptoms": [
            "high_fever", "abdominal_pain", "severe_headache", "fatigue",
            "loss_of_appetite", "general_weakness", "diarrhea"
        ],
        "mandatory_tests": ["Widal & Typhidot Blood Serology", "Complete Blood Count (CBC)"],
        "recommended_tests": ["Liver Function Test (LFT) with Bilirubin"],
        "specialist": "General Physician / Gastroenterologist",
        "severity": "Moderate to High",
        "urgency_score": 70,
        "advice": "Step-ladder fever pattern requires blood culture confirmation and targeted sensitive antibiotic therapy. Avoid heavy fibrous foods."
    },
    "Acute Gastroenteritis & Dehydration": {
        "symptoms": [
            "vomiting", "diarrhea", "abdominal_pain", "nausea",
            "general_weakness", "dizziness_lightheadedness", "reduced_urine_output"
        ],
        "mandatory_tests": ["Serum Electrolytes & Renal Function (KFT/Creatinine)"],
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "specialist": "Gastroenterologist",
        "severity": "Moderate",
        "urgency_score": 60,
        "advice": "Intense oral rehydration solution (WHO-ORS) or IV Ringer's Lactate if oral intake fails. Prevent acute pre-renal azotemia."
    },
    "Acute Cholecystitis / Gallstone Pathology": {
        "symptoms": [
            "right_upper_quadrant_pain", "vomiting", "nausea", "fever",
            "loss_of_appetite", "yellowing_of_eyes_skin_jaundice"
        ],
        "mandatory_tests": ["Abdominal Ultrasound (USG Whole Abdomen)", "Liver Function Test (LFT) with Bilirubin"],
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "specialist": "Gastrointestinal Surgeon",
        "severity": "Moderate to High",
        "urgency_score": 78,
        "advice": "Murphy's sign positive. NPO (nil per os), IV hydration, and surgical evaluation for laparoscopic cholecystectomy."
    },
    "Gastroesophageal Reflux (GERD) & Peptic Ulcer": {
        "symptoms": [
            "epigastric_burning_pain", "acidity_heartburn", "chest_tightness",
            "nausea", "loss_of_appetite", "bloating_abdominal_distension"
        ],
        "mandatory_tests": ["Complete Blood Count (CBC)"],
        "recommended_tests": ["12-Lead Electrocardiogram (ECG)"], # rule out atypical cardiac ischemia
        "specialist": "Gastroenterologist",
        "severity": "Low to Moderate",
        "urgency_score": 40,
        "advice": "Proton Pump Inhibitors (PPIs) 30 minutes before breakfast. Rule out cardiac etiology if chest tightness co-occurs."
    },
    "Acute Pyelonephritis / Complicated UTI": {
        "symptoms": [
            "flank_kidney_angle_pain", "high_fever", "chills", "dysuria_burning_urination",
            "urinary_frequency", "nausea", "hematuria_blood_in_urine"
        ],
        "mandatory_tests": ["Urinalysis Routine & Microscopic (Urine R/M)", "Complete Blood Count (CBC)"],
        "recommended_tests": ["Abdominal Ultrasound (USG Whole Abdomen)", "Serum Electrolytes & Renal Function (KFT/Creatinine)"],
        "specialist": "Urologist / Nephrologist",
        "severity": "Moderate to High",
        "urgency_score": 72,
        "advice": "Send urine culture prior to IV antibiotic administration. Monitor costovertebral tenderness and renal function."
    },
    "Deep Vein Thrombosis & Pulmonary Embolism Risk": {
        "symptoms": [
            "calf_tenderness_swelling", "breathlessness_shortness_of_breath",
            "chest_tightness", "palpitations_rapid_heartbeat", "hemoptysis_coughing_blood"
        ],
        "mandatory_tests": ["D-Dimer Quantitative Assay"],
        "recommended_tests": ["12-Lead Electrocardiogram (ECG)", "High-Resolution Chest CT Scan (HRCT)"],
        "specialist": "Vascular Specialist / Pulmonologist",
        "severity": "Critical / Emergency",
        "urgency_score": 92,
        "advice": "Emergency Wells Score calculation. Avoid vigorous calf massage which can dislodge clot. Immediate anticoagulation assessment."
    },
    "Migraine with Aura / Cluster Headache": {
        "symptoms": [
            "severe_headache", "photophobia_light_sensitivity", "nausea",
            "vomiting", "dizziness_lightheadedness", "vertigo_room_spinning"
        ],
        "mandatory_tests": [],
        "recommended_tests": ["Brain Non-Contrast CT Scan"], # only if atypical or first presentation
        "specialist": "Neurologist",
        "severity": "Moderate",
        "urgency_score": 45,
        "advice": "Abortive triptan therapy early during headache onset. Rest in dark quiet room. Keep headache trigger journal."
    },
    "Rheumatoid Arthritis / Systemic Inflammatory Arthropathy": {
        "symptoms": [
            "joint_pain_swelling", "morning_joint_stiffness", "body_muscle_aches",
            "fatigue", "general_weakness"
        ],
        "mandatory_tests": ["Rheumatoid Factor (RF) & Anti-CCP Panel", "C-Reactive Protein (CRP) & ESR"],
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "specialist": "Rheumatologist",
        "severity": "Moderate",
        "urgency_score": 50,
        "advice": "Early DMARD intervention within 12 weeks prevents irreversible joint erosions. Low impact exercise and joint protection."
    },
    "Allergic Dermatitis & Urticaria": {
        "symptoms": [
            "skin_rash", "itching_pruritus", "hives_urticaria",
            "skin_redness", "blisters"
        ],
        "mandatory_tests": ["Complete Blood Count (CBC)"],
        "recommended_tests": [],
        "specialist": "Dermatologist / Allergist",
        "severity": "Low to Moderate",
        "urgency_score": 35,
        "advice": "Second-generation antihistamines (Cetirizine/Levocetirizine), identify contact allergen, cool colloidal oatmeal compresses."
    },
    "Acute Viral Upper Respiratory Infection (Common Cold)": {
        "symptoms": [
            "runny_nose", "sneezing", "sore_throat", "mild_fever", "dry_cough", "fatigue"
        ],
        "mandatory_tests": [],
        "recommended_tests": ["Complete Blood Count (CBC)"],
        "specialist": "General Physician",
        "severity": "Low",
        "urgency_score": 20,
        "advice": "Symptomatic relief: warm saline gargles, hydration, paracetamol for fever. Antibiotics are strictly contraindicated."
    }
}
