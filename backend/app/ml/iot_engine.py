"""
IoT Medical Wearables Integration, Real-Time Vitals Streamer & Telemetry Anomaly Engine.
Patentable Mechanism:
- Multi-modal sensor telemetry aggregator with edge-anomaly classification.
- Dynamic critical threshold alerting with auto-escalation to hospital ER dashboards.
- Synthetic ECG waveform generator for synchronized telemetry streaming.
"""

import math
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

IOT_DEVICE_CATALOG = [
    {
        "device_type": "bp_monitor",
        "device_name": "Omron Platinum Wireless Blood Pressure Monitor",
        "device_uid": "OMRON-BP-9921",
        "firmware": "v4.1.2",
        "metrics": ["Systolic BP", "Diastolic BP", "Pulse Rate"]
    },
    {
        "device_type": "glucose_sensor",
        "device_name": "Dexcom G7 Continuous Glucose Monitor (CGM)",
        "device_uid": "DEXCOM-CGM-4410",
        "firmware": "v2.0.8",
        "metrics": ["Interstitial Blood Glucose"]
    },
    {
        "device_type": "ecg_sensor",
        "device_name": "KardiaMobile 6-Lead ECG Smart Patch",
        "device_uid": "KARDIA-ECG-1029",
        "firmware": "v5.2.0",
        "metrics": ["Heart Rate", "Rhythm Waveform", "QT Interval"]
    },
    {
        "device_type": "pulse_oximeter",
        "device_name": "Wellue O2Ring Continuous SpO2 Sensor",
        "device_uid": "WELLUE-SPO2-8832",
        "firmware": "v1.8.4",
        "metrics": ["SpO2 Oxygen Saturation", "Perfusion Index"]
    }
]

def generate_ecg_waveform(samples: int = 40, heart_rate: float = 75.0) -> List[float]:
    """
    Generates realistic Lead-II ECG P-Q-R-S-T voltage waveform points for live canvas plotting.
    """
    points = []
    for i in range(samples):
        t = (i % 20) / 20.0
        # P wave
        val = 0.0
        if 0.1 <= t < 0.2:
            val += 0.15 * math.sin((t - 0.1) / 0.1 * math.pi)
        # Q wave
        elif 0.28 <= t < 0.32:
            val -= 0.15
        # R wave spike
        elif 0.32 <= t < 0.40:
            val += 1.0 * math.sin((t - 0.32) / 0.08 * math.pi)
        # S wave
        elif 0.40 <= t < 0.46:
            val -= 0.25
        # T wave
        elif 0.55 <= t < 0.75:
            val += 0.25 * math.sin((t - 0.55) / 0.2 * math.pi)
        
        # Add slight natural jitter
        val += random.uniform(-0.02, 0.02)
        points.append(round(val, 3))
    return points

def evaluate_vital_thresholds(metric_type: str, primary: float, secondary: Optional[float] = None) -> Tuple[str, bool, str]:
    """
    Evaluates clinical severity thresholds.
    Returns: (alert_severity, is_anomaly, alert_message)
    """
    if metric_type == "blood_pressure":
        sys = primary
        dia = secondary or 80.0
        if sys >= 180.0 or dia >= 120.0:
            return "CRITICAL", True, f"CRITICAL HYPERTENSIVE CRISIS ({int(sys)}/{int(dia)} mmHg) - Immediate ER triage required!"
        elif sys >= 140.0 or dia >= 90.0:
            return "WARNING", True, f"Hypertensive Reading ({int(sys)}/{int(dia)} mmHg) - Clinical review advised."
        elif sys < 90.0 or dia < 60.0:
            return "WARNING", True, f"Hypotension Alert ({int(sys)}/{int(dia)} mmHg) - Low vascular perfusion."
        return "NORMAL", False, f"Optimal Blood Pressure ({int(sys)}/{int(dia)} mmHg)"

    elif metric_type == "glucose":
        val = primary
        if val >= 300.0:
            return "CRITICAL", True, f"CRITICAL HYPERGLYCEMIA ({int(val)} mg/dL) - Risk of Diabetic Ketoacidosis!"
        elif val < 60.0:
            return "CRITICAL", True, f"CRITICAL SEVERE HYPOGLYCEMIA ({int(val)} mg/dL) - Immediate glucose intake needed!"
        elif val >= 180.0:
            return "WARNING", True, f"High Glucose ({int(val)} mg/dL) - Glycemic control excursion."
        elif val < 70.0:
            return "WARNING", True, f"Borderline Low Glucose ({int(val)} mg/dL) - Fast-acting carbohydrate advised."
        return "NORMAL", False, f"Target Blood Glucose ({int(val)} mg/dL)"

    elif metric_type == "spo2":
        val = primary
        if val < 90.0:
            return "CRITICAL", True, f"CRITICAL HYPOXEMIA ({int(val)}%) - Severe respiratory compromise, ER oxygen needed!"
        elif val < 94.0:
            return "WARNING", True, f"Borderline Low Oxygen ({int(val)}%) - Check airway and consult physician."
        return "NORMAL", False, f"Healthy SpO2 Saturation ({int(val)}%)"

    elif metric_type == "heart_rate":
        val = primary
        if val > 140.0:
            return "CRITICAL", True, f"CRITICAL TACHYCARDIA ({int(val)} bpm) - Arrhythmia or acute distress."
        elif val < 45.0:
            return "CRITICAL", True, f"CRITICAL BRADYCARDIA ({int(val)} bpm) - Severe sinus deceleration."
        elif val > 105.0:
            return "WARNING", True, f"Elevated Pulse ({int(val)} bpm) - Sinus tachycardia."
        elif val < 55.0:
            return "WARNING", True, f"Low Heart Rate ({int(val)} bpm) - Mild bradycardia."
        return "NORMAL", False, f"Normal Sinus Rhythm ({int(val)} bpm)"

    elif metric_type == "temperature":
        val = primary
        if val >= 103.5:
            return "CRITICAL", True, f"CRITICAL HYPERPYREXIA ({val:.1f}°F) - Severe febrile illness."
        elif val >= 100.4:
            return "WARNING", True, f"Febrile State ({val:.1f}°F) - Active fever."
        return "NORMAL", False, f"Normal Body Temperature ({val:.1f}°F)"

    return "NORMAL", False, f"Reading: {primary}"

def generate_telemetry_reading(metric_type: str, simulate_anomaly: bool = False) -> Dict[str, Any]:
    """
    Synthesizes a realistic IoT telemetry reading.
    """
    if metric_type == "blood_pressure":
        if simulate_anomaly:
            sys = round(random.uniform(182.0, 195.0), 1)
            dia = round(random.uniform(112.0, 125.0), 1)
        else:
            sys = round(random.uniform(118.0, 134.0), 1)
            dia = round(random.uniform(76.0, 86.0), 1)
        sev, is_a, msg = evaluate_vital_thresholds("blood_pressure", sys, dia)
        return {
            "metric_type": "blood_pressure",
            "primary_value": sys,
            "secondary_value": dia,
            "unit": "mmHg",
            "is_anomaly": is_a,
            "alert_severity": sev,
            "alert_message": msg,
            "ecg_waveform_points": None
        }

    elif metric_type == "glucose":
        if simulate_anomaly:
            val = round(random.uniform(305.0, 340.0), 1)
        else:
            val = round(random.uniform(95.0, 142.0), 1)
        sev, is_a, msg = evaluate_vital_thresholds("glucose", val)
        return {
            "metric_type": "glucose",
            "primary_value": val,
            "secondary_value": None,
            "unit": "mg/dL",
            "is_anomaly": is_a,
            "alert_severity": sev,
            "alert_message": msg,
            "ecg_waveform_points": None
        }

    elif metric_type == "spo2":
        if simulate_anomaly:
            val = round(random.uniform(86.0, 89.0), 1)
        else:
            val = round(random.uniform(97.0, 99.0), 1)
        sev, is_a, msg = evaluate_vital_thresholds("spo2", val)
        return {
            "metric_type": "spo2",
            "primary_value": val,
            "secondary_value": None,
            "unit": "%",
            "is_anomaly": is_a,
            "alert_severity": sev,
            "alert_message": msg,
            "ecg_waveform_points": None
        }

    elif metric_type == "heart_rate" or metric_type == "ecg_sensor":
        if simulate_anomaly:
            hr = round(random.uniform(142.0, 160.0), 1)
        else:
            hr = round(random.uniform(68.0, 84.0), 1)
        sev, is_a, msg = evaluate_vital_thresholds("heart_rate", hr)
        ecg = generate_ecg_waveform(samples=40, heart_rate=hr)
        return {
            "metric_type": "heart_rate",
            "primary_value": hr,
            "secondary_value": None,
            "unit": "bpm",
            "is_anomaly": is_a,
            "alert_severity": sev,
            "alert_message": msg,
            "ecg_waveform_points": ecg
        }

    # Default
    return {
        "metric_type": "temperature",
        "primary_value": 98.6,
        "secondary_value": None,
        "unit": "°F",
        "is_anomaly": False,
        "alert_severity": "NORMAL",
        "alert_message": "Normal temperature",
        "ecg_waveform_points": None
    }
