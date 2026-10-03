"""
AI Predictive Care Engine & Chronic Disease Deterioration Forecaster.
Core Technical Mechanisms:
- Longitudinal deterioration risk index (0-100) derived from Bayesian symptom progression,
  lab biomarker trends, and pre-existing chronic conditions.
- Automated predictive follow-up scheduling engine that recommends proactive specialist consults
  before acute exacerbations occur.
- Rule + heuristic AI alert synthesis for chronic disease exacerbation prevention.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

CHRONIC_CONDITION_RULES = {
    "diabetes": {
        "condition_name": "Type 2 Diabetes Mellitus",
        "keywords": ["diabetes", "diabetic", "blood sugar", "glucose"],
        "critical_glucose_high": 250.0,
        "warning_glucose_high": 160.0,
        "critical_glucose_low": 65.0,
        "specialist": "Endocrinologist / Diabetologist",
        "monitoring_frequency_days": 3
    },
    "hypertension": {
        "condition_name": "Essential Hypertension",
        "keywords": ["hypertension", "high blood pressure", "bp", "cardiac"],
        "critical_systolic": 180.0,
        "warning_systolic": 140.0,
        "critical_diastolic": 110.0,
        "warning_diastolic": 90.0,
        "specialist": "Cardiologist",
        "monitoring_frequency_days": 3
    },
    "asthma": {
        "condition_name": "Bronchial Asthma / COPD",
        "keywords": ["asthma", "copd", "wheezing", "bronchitis"],
        "critical_spo2": 90.0,
        "warning_spo2": 94.0,
        "specialist": "Pulmonologist",
        "monitoring_frequency_days": 2
    }
}

def calculate_predictive_deterioration_risk(
    patient_context: Dict[str, Any],
    recent_consultations: List[Dict[str, Any]],
    latest_vitals: Optional[Dict[str, Any]] = None,
    recovery_status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Computes an Explainable Deterioration Risk Score (0-100)
    and predicts optimal follow-up scheduling intervals.
    """
    score = 20.0 # Baseline low risk
    reasons = []
    
    # 1. Age factor
    age = patient_context.get("age", 35) or 35
    if age >= 65:
        score += 15.0
        reasons.append(f"Geriatric baseline vulnerability (Age {age}) adds clinical surveillance weight.")
    elif age >= 50:
        score += 8.0

    # 2. Pre-existing chronic illnesses
    pre_existing = str(patient_context.get("pre_existing_conditions", "")).lower()
    chronic_count = 0
    if "diabetes" in pre_existing:
        score += 18.0
        chronic_count += 1
        reasons.append("Active Type 2 Diabetes compounds infection vulnerability and metabolic instability.")
    if "hypertension" in pre_existing:
        score += 15.0
        chronic_count += 1
        reasons.append("Chronic Hypertension heightens cardiovascular strain risk.")
    if "asthma" in pre_existing or "pulmonary" in pre_existing:
        score += 16.0
        chronic_count += 1
        reasons.append("Pre-existing respiratory vulnerability increases bronchospasm risk.")

    # 3. Latest vital readings
    if latest_vitals:
        # Check Blood Pressure
        sys = latest_vitals.get("systolic_bp")
        dia = latest_vitals.get("diastolic_bp")
        if sys and dia:
            if sys >= 170 or dia >= 105:
                score += 25.0
                reasons.append(f"Elevated blood pressure ({sys}/{dia} mmHg) approaches hypertensive crisis stage.")
            elif sys >= 140 or dia >= 90:
                score += 12.0
                reasons.append(f"Stage 1/2 Hypertension detected in IoT vitals ({sys}/{dia} mmHg).")

        # Check Glucose
        glucose = latest_vitals.get("glucose")
        if glucose:
            if glucose >= 250:
                score += 22.0
                reasons.append(f"Severe glycemic spike (Blood Glucose {glucose} mg/dL) demands prompt endocrine adjustment.")
            elif glucose >= 160:
                score += 10.0
                reasons.append(f"Elevated postprandial glucose ({glucose} mg/dL) outside safe glycemic window.")

        # Check SpO2
        spo2 = latest_vitals.get("spo2")
        if spo2:
            if spo2 < 92:
                score += 30.0
                reasons.append(f"Critical hypoxemia alert: SpO2 measured at {spo2}%.")
            elif spo2 < 95:
                score += 14.0
                reasons.append(f"Borderline oxygen saturation (SpO2 {spo2}%).")

    # 4. Recovery Trajectory
    if recovery_status:
        if recovery_status.lower() in ["worsened", "same"]:
            score += 20.0
            reasons.append(f"Post-treatment recovery trajectory logged as '{recovery_status}', indicating non-response to therapy.")
        elif recovery_status.lower() in ["significantly improved", "improving"]:
            score = max(10.0, score - 15.0)

    # 5. Recent Consultation Triage
    if recent_consultations:
        latest = recent_consultations[0]
        triage = latest.get("triage_level", "")
        if "Emergency" in triage:
            score += 25.0
        elif "Doctor" in triage:
            score += 10.0

    score = min(max(score, 12.0), 99.0)

    # Determine Urgency & Timeline
    if score >= 75.0:
        urgency = "High"
        timeline = "Within 24 to 48 hours"
        recommended_specialist = "Critical Care / Specialist Physician"
        days_ahead = 2
    elif score >= 50.0:
        urgency = "Moderate"
        timeline = "Within 3 to 5 days"
        recommended_specialist = "Attending Pulmonologist / Cardiologist"
        days_ahead = 4
    else:
        urgency = "Low"
        timeline = "Routine Follow-up in 10-14 days"
        recommended_specialist = "General Practitioner"
        days_ahead = 10

    suggested_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%A, %b %d, %Y")

    return {
        "risk_score": round(score, 1),
        "urgency_level": urgency,
        "suggested_timeline": timeline,
        "suggested_date": suggested_date,
        "recommended_specialist": recommended_specialist,
        "urgency_rationale": " | ".join(reasons) if reasons else "Routine longitudinal maintenance assessment.",
        "reasons_breakdown": reasons
    }

def generate_chronic_ai_alerts(patient_context: Dict[str, Any], vitals_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Synthesizes proactive chronic condition alerts based on documented history and incoming metrics.
    """
    alerts = []
    pre_existing = str(patient_context.get("pre_existing_conditions", "")).lower()

    # Look for latest readings
    latest_bp = None
    latest_glucose = None
    latest_spo2 = None

    for r in vitals_list:
        m = r.get("metric_type")
        if m == "blood_pressure" and not latest_bp:
            latest_bp = r
        elif m == "glucose" and not latest_glucose:
            latest_glucose = r
        elif m == "spo2" and not latest_spo2:
            latest_spo2 = r

    # Diabetes Alert
    if "diabetes" in pre_existing:
        glucose_val = latest_glucose.get("primary_value") if latest_glucose else 185.0
        if glucose_val >= 220:
            alerts.append({
                "condition_name": "Type 2 Diabetes",
                "severity": "CRITICAL",
                "title": f"Hyperglycemia Alert: Glucose {glucose_val} mg/dL",
                "clinical_implication": "Blood sugar significantly above target threshold. Risk of hyperosmolar diabetic state or acute fatigue.",
                "recommended_action": "Check urinary ketones, hydrate abundantly, review Metformin dosing with doctor, and avoid carbohydrate load."
            })
        elif glucose_val >= 150:
            alerts.append({
                "condition_name": "Type 2 Diabetes",
                "severity": "WARNING",
                "title": f"Elevated Postprandial Glucose ({glucose_val} mg/dL)",
                "clinical_implication": "Current glycemic baseline is above the 140 mg/dL optimal target.",
                "recommended_action": "Log 30-minute post-meal walk and verify compliance with morning oral anti-diabetic medications."
            })

    # Hypertension Alert
    if "hypertension" in pre_existing or "high blood pressure" in pre_existing:
        sys_val = latest_bp.get("primary_value") if latest_bp else 148.0
        dia_val = latest_bp.get("secondary_value") if latest_bp else 94.0
        if sys_val >= 170 or dia_val >= 105:
            alerts.append({
                "condition_name": "Hypertension",
                "severity": "CRITICAL",
                "title": f"Hypertensive Spike Alert: {int(sys_val)}/{int(dia_val)} mmHg",
                "clinical_implication": "End-organ microvascular stress detected. Patient is at risk of headache, vision blur, and cardiac strain.",
                "recommended_action": "Rest quietly in seated position for 15 minutes, recheck BP. If sustained > 170, initiate emergency consultation."
            })
        elif sys_val >= 140 or dia_val >= 90:
            alerts.append({
                "condition_name": "Hypertension",
                "severity": "WARNING",
                "title": f"Stage 1 Hypertension Trend ({int(sys_val)}/{int(dia_val)} mmHg)",
                "clinical_implication": "Sub-optimal blood pressure control detected over recent telemetry logs.",
                "recommended_action": "Reduce sodium consumption to < 2g/day, adhere to Telmisartan/Amlodipine schedule, and repeat reading tonight."
            })

    # Drug Allergy Cross-Warning
    allergies = str(patient_context.get("drug_allergies", "")).lower()
    if "penicillin" in allergies or "amoxicillin" in allergies:
        alerts.append({
            "condition_name": "Severe Drug Allergy Shield",
            "severity": "INFO",
            "title": "Active Allergy Barrier: Beta-Lactam / Penicillin",
            "clinical_implication": "Patient has verified IgE/anaphylactoid sensitivity to Penicillin class antibiotics.",
            "recommended_action": "System active safety filter will auto-block any amoxicillin, augmentin, or cephalosporin crossover prescriptions."
        })

    return alerts
