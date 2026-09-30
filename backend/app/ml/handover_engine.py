"""
AI-Generated Clinical Handover Engine.
Produces structured SBAR (Situation, Background, Assessment, Recommendation)
clinical summaries for the attending physician before patient consultation.
"""

from typing import Dict, Any, List

def generate_sbar_handover(
    patient_info: Dict[str, Any],
    symptoms: List[str],
    qa_answers: Dict[str, Any],
    predicted_disease: str,
    confidence: float,
    triage_data: Dict[str, Any],
    biomarkers: Dict[str, Any],
    patient_notes: str = ""
) -> Dict[str, Any]:
    """
    Synthesizes patient data, AI triage assessment, and report findings
    into a structured SBAR clinical handover for physicians.
    """
    readable_symptoms = [s.replace('_', ' ').title() for s in symptoms]
    
    # Situation
    duration = qa_answers.get("duration_days", "Recent onset")
    severity = qa_answers.get("severity_scale", "Moderate discomfort")
    situation = {
        "chief_complaint": f"Patient presents with {', '.join(readable_symptoms)}.",
        "onset_duration": duration,
        "pain_intensity_scale": severity,
        "patient_stated_concern": patient_notes or "Primary evaluation requested."
    }

    # Background
    age = patient_info.get("age", "Not specified")
    gender = patient_info.get("gender", "Not specified")
    pre_existing = patient_info.get("pre_existing_conditions") or "None reported"
    current_meds = patient_info.get("current_medications") or "None reported"
    drug_allergies = patient_info.get("drug_allergies") or "No known drug allergies (NKDA)"
    prior_meds_taken = qa_answers.get("prior_meds_taken", "None reported")

    background = {
        "demographics": f"Age: {age}, Gender: {gender}",
        "pre_existing_conditions": pre_existing,
        "regular_medications": current_meds,
        "drug_allergies": drug_allergies,
        "medication_already_taken_for_this_episode": prior_meds_taken
    }

    # Assessment
    triage_level = triage_data.get("triage_level", "Doctor Consultation")
    abnormal_labs = biomarkers.get("abnormal_flags", []) if biomarkers else []
    extracted_params = biomarkers.get("extracted_parameters", {}) if biomarkers else {}
    radiology_findings = biomarkers.get("radiology_findings", []) if biomarkers else []

    assessment = {
        "ai_triage_level": triage_level,
        "probable_diagnosis": f"{predicted_disease} ({confidence}% confidence)",
        "abnormal_biomarkers_identified": abnormal_labs or ["No critical lab anomalies detected."],
        "key_lab_values": extracted_params,
        "imaging_impressions": radiology_findings or ["No scans attached."]
    }

    # Recommendation
    recommendation = {
        "suggested_clinical_inquiries": [
            f"Correlate symptom onset ({duration}) with physical auscultation / examination.",
            "Verify current medication adherence and assess response to prior OTC medicines.",
            "Review flagged biomarkers with patient and discuss diagnostic imaging."
        ],
        "urgent_considerations": (
            "Immediate emergency stabilization advised due to red-flag symptoms."
            if triage_level == "Emergency Care" else
            "Routine clinical workup and tailored pharmacotherapy indicated."
        )
    }

    # Formatted plain text version for print / quick view
    formatted_text = f"""--- CLINICAL HANDOVER SUMMARY (SBAR) ---
PATIENT: {patient_info.get('full_name', 'Patient')} | {background['demographics']}

[S] SITUATION:
• Chief Complaints: {', '.join(readable_symptoms)}
• Duration: {duration} | Discomfort: {severity}
• Notes: {situation['patient_stated_concern']}

[B] BACKGROUND:
• Pre-existing Conditions: {pre_existing}
• Current Medications: {current_meds}
• Known Drug Allergies: {drug_allergies}
• Self-medication taken: {prior_meds_taken}

[A] ASSESSMENT:
• AI Triage Urgency: {triage_level.upper()}
• Suspected Etiology: {predicted_disease} ({confidence}% match)
• Lab Findings: {', '.join(abnormal_labs) if abnormal_labs else 'Within normal range'}
• Radiology: {', '.join(radiology_findings) if radiology_findings else 'N/A'}

[R] RECOMMENDATION:
• Review indicated diagnostics and ensure allergy-safe pharmacotherapy.
"""

    return {
        "situation": situation,
        "background": background,
        "assessment": assessment,
        "recommendation": recommendation,
        "formatted_text": formatted_text
    }
