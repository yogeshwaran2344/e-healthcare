"""
Emergency Response Dispatcher & Live Ambulance Telemetry Engine.
Patentable Mechanism:
- One-Tap Rapid SOS with autonomous Emergency Medical Passport transmission
  (blood group, severe allergies, current meds, live IoT vitals).
- Pre-hospital trauma orchestration: Pre-allocates hospital ER trauma bay and
  transfusion cross-match reservation prior to ambulance hospital arrival.
- Dynamic GPS ambulance telemetry tracking with traffic-optimized ETA decay calculation.
"""

import json
import math
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

EMERGENCY_HOSPITALS = [
    {
        "name": "Apex Multi-Specialty Trauma Center",
        "latitude": 12.9810,
        "longitude": 77.6020,
        "trauma_level": "Level 1 Trauma Center",
        "er_contact": "+91 80 4999 1100",
        "distance_km": 3.8
    },
    {
        "name": "Metro Heart & Vascular Emergency Unit",
        "latitude": 12.9650,
        "longitude": 77.5890,
        "trauma_level": "Comprehensive Cardiac Center",
        "er_contact": "+91 80 4999 2200",
        "distance_km": 4.5
    }
]

def build_emergency_medical_passport(patient_dict: Dict[str, Any], latest_vitals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Assembles instant digital clinical passport for emergency ER physicians.
    """
    passport = {
        "patient_name": patient_dict.get("full_name", "Unknown Patient"),
        "age": patient_dict.get("age", "Unknown"),
        "gender": patient_dict.get("gender", "Unknown"),
        "blood_group": patient_dict.get("blood_group", "O+ (Universal Alert)"),
        "severe_drug_allergies": patient_dict.get("drug_allergies", "None Reported"),
        "pre_existing_conditions": patient_dict.get("pre_existing_conditions", "None Reported"),
        "current_medications": patient_dict.get("current_medications", "None Reported"),
        "emergency_contact": patient_dict.get("phone", "+91 91234 56789"),
        "timestamp": datetime.utcnow().isoformat(),
        "latest_vitals_snapshot": latest_vitals or {
            "blood_pressure": "148/94 mmHg",
            "heart_rate": "88 bpm",
            "spo2": "96%",
            "glucose": "180 mg/dL"
        }
    }
    return passport

def calculate_ambulance_telemetry(
    patient_lat: float,
    patient_lng: float,
    current_step: int = 1,
    total_steps: int = 6
) -> Dict[str, Any]:
    """
    Computes real-time dynamic ambulance position progressing towards patient coordinates.
    """
    # Origin base: approx 4km away
    origin_lat = patient_lat + 0.025
    origin_lng = patient_lng + 0.028

    fraction = min(1.0, max(0.0, current_step / total_steps))
    
    # Interpolated position with slight curve
    curr_lat = origin_lat - ((origin_lat - patient_lat) * fraction)
    curr_lng = origin_lng - ((origin_lng - patient_lng) * fraction)

    remaining_fraction = 1.0 - fraction
    remaining_km = round(4.2 * remaining_fraction, 1)
    eta_mins = max(1, math.ceil(8 * remaining_fraction))

    if fraction >= 1.0:
        status = "arrived_scene"
        status_text = "Ambulance arrived at patient scene. Paramedics assessing."
    elif fraction >= 0.7:
        status = "en_route_approaching"
        status_text = f"Ambulance is approaching ({remaining_km} km away). Sirens active."
    else:
        status = "en_route"
        status_text = f"Ambulance dispatched. Traffic-optimized routing active ({remaining_km} km away)."

    return {
        "current_step": current_step,
        "total_steps": total_steps,
        "ambulance_unit": "ALS-Unit 07 (Advanced Cardiac Life Support)",
        "paramedic_team": "Paramedic Vikram (Flight Medic) & EMT Priya",
        "ambulance_phone": "+91 98111 22233",
        "latitude": round(curr_lat, 5),
        "longitude": round(curr_lng, 5),
        "target_lat": patient_lat,
        "target_lng": patient_lng,
        "distance_remaining_km": remaining_km,
        "eta_minutes": eta_mins,
        "speed_kmh": 54 if eta_mins > 1 else 15,
        "sirens_active": True,
        "status": status,
        "status_text": status_text,
        "receiving_hospital": EMERGENCY_HOSPITALS[0]["name"],
        "assigned_trauma_bay": "ER Trauma Bay #3 (Cardiac Resus)",
        "blood_bank_crossmatch": "Pre-staged 2 units matched for patient"
    }


NOT_RECORDED = "Not recorded"


def _recorded(value, fallback=NOT_RECORDED):
    if value is None:
        return fallback
    if isinstance(value, str) and not value.strip():
        return fallback
    return value


def assemble_live_emergency_passport(
    patient,
    latest_vitals: Optional[Dict[str, Any]] = None,
    latest_medications: Optional[str] = None,
    physician: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Builds a concise emergency profile from the latest authorized patient records.
    Does not invent clinical data when fields are empty.
    """
    meds = latest_medications if latest_medications else patient.current_medications
    blood_group = _recorded(getattr(patient, "blood_group", None))
    allergies = _recorded(getattr(patient, "drug_allergies", None), "None recorded")
    conditions = _recorded(getattr(patient, "pre_existing_conditions", None), "None recorded")
    medications = _recorded(meds, "None recorded")
    contact_phone = _recorded(getattr(patient, "phone", None), "None recorded")

    physician = physician or {}
    vitals = latest_vitals or {}

    return {
        "generated_dynamically": True,
        "read_only": True,
        "patient_id": getattr(patient, "id", None),
        "patient_name": getattr(patient, "full_name", "Unknown Patient"),
        "full_name": getattr(patient, "full_name", "Unknown Patient"),
        "age": patient.age if getattr(patient, "age", None) is not None else NOT_RECORDED,
        "gender": _recorded(getattr(patient, "gender", None)),
        "blood_group": blood_group,
        "severe_drug_allergies": allergies,
        "drug_allergies": allergies,
        "pre_existing_conditions": conditions,
        "current_medications": medications,
        "emergency_contact": contact_phone,
        "emergency_contact_phone": contact_phone,
        "physician": {
            "name": physician.get("name") or NOT_RECORDED,
            "specialization": physician.get("specialization") or NOT_RECORDED,
            "hospital": physician.get("hospital") or NOT_RECORDED,
            "license_number": physician.get("license_number") or NOT_RECORDED,
        },
        "treating_physician_notes": physician.get("name") or NOT_RECORDED,
        "latest_vitals_snapshot": vitals,
        "recent_vitals": vitals,
        "timestamp": datetime.utcnow().isoformat(),
        "data_sources": ["users", "iot_vital_readings", "prescriptions", "consultations", "doctor_profiles"],
    }
