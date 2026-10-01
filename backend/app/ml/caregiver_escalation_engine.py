"""
Context-Aware Caregiver Alerts Engine
Multi-Tier Severity Escalation System based on Predictive Health Risk Scoring
Patent angle: 'A caregiver alert system that prioritizes and escalates notifications based on predictive health risk scoring.'
"""

from typing import Dict, Any, List

def evaluate_contextual_caregiver_alert(
    vitals: Dict[str, Any],
    missed_doses_count: int = 0,
    patient_name: str = "Rahul Verma"
) -> Dict[str, Any]:
    """
    Evaluates patient vital signals and compliance trajectory, formulating tiered escalation alerts:
    - Level 1: STABLE (Normal telemetry, zero interruption)
    - Level 2: MILD DEVIATION (Notify caregiver only for gentle check-in)
    - Level 3: MODERATE VULNERABILITY (Caregiver alert + Doctor OPD consultation flagged)
    - Level 4: CRITICAL EMERGENCY (Immediate Caregiver Alarm + Doctor ER Trauma Bay + 1-Tap SOS Dispatch)
    """
    hr = float(vitals.get("hr", 75))
    spo2 = float(vitals.get("spo2", 98))
    systolic_bp = float(vitals.get("bp_sys", 120))
    diastolic_bp = float(vitals.get("bp_dia", 80))
    temp = float(vitals.get("temp", 98.6))

    # Level 4: Critical Emergency
    if spo2 < 90 or hr > 135 or hr < 42 or systolic_bp > 185 or systolic_bp < 85:
        reasons = []
        if spo2 < 90: reasons.append(f"Severe Hypoxemia (SpO2 {spo2}%)")
        if hr > 135: reasons.append(f"Severe Tachycardia (HR {hr} bpm)")
        if hr < 42: reasons.append(f"Critical Bradycardia (HR {hr} bpm)")
        if systolic_bp > 185: reasons.append(f"Hypertensive Crisis (BP {systolic_bp}/{diastolic_bp} mmHg)")
        
        return {
            "tier_level": 4,
            "tier_code": "LEVEL_4_CRITICAL_EMERGENCY",
            "tier_badge": "CRITICAL EMERGENCY (SOS)",
            "tier_color": "danger",
            "notify_caregiver": True,
            "notify_doctor": True,
            "trigger_emergency_sos": True,
            "channels": ["Immediate Caregiver Voice Call", "Attending ER Physician HUD", "Automated GPS Ambulance Corridor"],
            "primary_trigger": ", ".join(reasons),
            "caregiver_message": f"CRITICAL HEALTH ALERT for {patient_name}: {', '.join(reasons)}. Automated 1-Tap SOS has been dispatched. Reserved Trauma Bay staged.",
            "recommended_action": "Immediate emergency hospitalization in progress. Please contact patient or meet emergency crew at ER."
        }

    # Level 3: Moderate Risk
    if spo2 <= 93 or hr > 115 or systolic_bp >= 155 or diastolic_bp >= 95 or missed_doses_count >= 2:
        reasons = []
        if spo2 <= 93: reasons.append(f"Suboptimal Oxygen Saturation (SpO2 {spo2}%)")
        if hr > 115: reasons.append(f"Tachycardia (HR {hr} bpm)")
        if systolic_bp >= 155: reasons.append(f"Stage 2 Hypertension (BP {systolic_bp}/{diastolic_bp} mmHg)")
        if missed_doses_count >= 2: reasons.append(f"{missed_doses_count} Consecutive Missed Doses")

        return {
            "tier_level": 3,
            "tier_code": "LEVEL_3_MODERATE_VULNERABILITY",
            "tier_badge": "MODERATE VULNERABILITY",
            "tier_color": "warning",
            "notify_caregiver": True,
            "notify_doctor": True,
            "trigger_emergency_sos": False,
            "channels": ["High-Priority Caregiver Notification", "Doctor OPD Priority Queue"],
            "primary_trigger": ", ".join(reasons),
            "caregiver_message": f"Health Care Alert for {patient_name}: {', '.join(reasons)}. A tele-consultation follow-up has been flagged for attending physician review.",
            "recommended_action": "Ensure patient rests in seated position, takes prescribed medication, and connects with attending doctor."
        }

    # Level 2: Mild Deviation
    if hr > 100 or systolic_bp >= 135 or temp >= 100.4 or missed_doses_count == 1:
        reasons = []
        if hr > 100: reasons.append(f"Elevated Resting Heart Rate ({hr} bpm)")
        if systolic_bp >= 135: reasons.append(f"Borderline Systolic BP ({systolic_bp} mmHg)")
        if temp >= 100.4: reasons.append(f"Low-grade Fever ({temp} °F)")
        if missed_doses_count == 1: reasons.append("1 Missed Medication Dose")

        return {
            "tier_level": 2,
            "tier_code": "LEVEL_2_MILD_CARE_ALERT",
            "tier_badge": "MILD DEVIATION",
            "tier_color": "info",
            "notify_caregiver": True,
            "notify_doctor": False,
            "trigger_emergency_sos": False,
            "channels": ["Caregiver Push Message (WhatsApp/SMS)"],
            "primary_trigger": ", ".join(reasons),
            "caregiver_message": f"Caregiver Notice for {patient_name}: Mild vital deviation detected ({', '.join(reasons)}).",
            "recommended_action": "Check in on patient hydration and confirm daily medication routine."
        }

    # Level 1: Normal
    return {
        "tier_level": 1,
        "tier_code": "LEVEL_1_NORMAL",
        "tier_badge": "STABLE",
        "tier_color": "success",
        "notify_caregiver": False,
        "notify_doctor": False,
        "trigger_emergency_sos": False,
        "channels": [],
        "primary_trigger": "All vital parameters within target baseline",
        "caregiver_message": f"{patient_name} vital parameters are stable.",
        "recommended_action": "No intervention required. Standard monitoring active."
    }
