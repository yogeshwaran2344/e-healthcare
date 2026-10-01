"""
Smart Adaptive Reminders Engine
Dynamic Behavioral Medicine Compliance & AI Rescheduling System
Mathematical/Algorithmic Basis:
- Analyzes empirical medication confirmation delay distribution: Delta_t = t_confirmed - t_scheduled
- Computes sample mean mu_delay and variance sigma_delay
- Identifies persistent behavioral habit shifts (e.g., consistent commute or mealtime delays)
- Reschedules nominal reminder windows to maximize patient adherence probability P(compliance)
"""

from typing import List, Dict, Any
from datetime import datetime, time, timedelta

DEFAULT_SCHEDULES = [
    {
        "id": 1,
        "medicine_name": "Metformin 500mg",
        "condition": "Type 2 Diabetes Mellitus",
        "prescribed_time": "08:00",
        "current_reminder_time": "09:15",
        "dosage": "1 Tablet with breakfast",
        "is_adapted": True,
        "shift_minutes": 75,
        "adherence_rate_pct": 92.5,
        "adaptation_rationale": "Patient consistently confirmed intake +75 mins after nominal 08:00 AM prescription due to morning commute. AI rescheduled reminder window to 09:15 AM, improving 14-day adherence from 68% to 92.5%.",
        "history": [
            {"date": "2026-09-28", "scheduled": "08:00", "confirmed": "09:18", "delay_minutes": 78},
            {"date": "2026-09-29", "scheduled": "08:00", "confirmed": "09:12", "delay_minutes": 72},
            {"date": "2026-09-30", "scheduled": "08:00", "confirmed": "09:15", "delay_minutes": 75},
            {"date": "2026-10-01", "scheduled": "09:15", "confirmed": "09:14", "delay_minutes": -1}
        ]
    },
    {
        "id": 2,
        "medicine_name": "Atorvastatin 20mg",
        "condition": "Hyperlipidemia / CAD Risk Shield",
        "prescribed_time": "20:00",
        "current_reminder_time": "21:30",
        "dosage": "1 Tablet post dinner",
        "is_adapted": True,
        "shift_minutes": 90,
        "adherence_rate_pct": 96.0,
        "adaptation_rationale": "Evening dinner routine occurs at 21:00 PM. Reminder shifted +90 mins to align with postprandial window.",
        "history": [
            {"date": "2026-09-28", "scheduled": "20:00", "confirmed": "21:35", "delay_minutes": 95},
            {"date": "2026-09-29", "scheduled": "20:00", "confirmed": "21:28", "delay_minutes": 88},
            {"date": "2026-09-30", "scheduled": "20:00", "confirmed": "21:30", "delay_minutes": 90}
        ]
    },
    {
        "id": 3,
        "medicine_name": "Telmisartan 40mg",
        "condition": "Essential Hypertension",
        "prescribed_time": "09:00",
        "current_reminder_time": "09:00",
        "dosage": "1 Tablet morning",
        "is_adapted": False,
        "shift_minutes": 0,
        "adherence_rate_pct": 98.0,
        "adaptation_rationale": "High baseline adherence (< 5 mins variance). Fixed schedule maintained.",
        "history": [
            {"date": "2026-09-28", "scheduled": "09:00", "confirmed": "09:04", "delay_minutes": 4},
            {"date": "2026-09-29", "scheduled": "09:00", "confirmed": "09:02", "delay_minutes": 2},
            {"date": "2026-09-30", "scheduled": "09:00", "confirmed": "08:58", "delay_minutes": -2}
        ]
    }
]

def calculate_adaptive_reminder(
    prescribed_time: str,
    confirmation_delays: List[int]
) -> Dict[str, Any]:
    """
    Evaluates delay distribution to formulate an optimal adapted reminder time.
    """
    if not confirmation_delays:
        return {
            "is_adapted": False,
            "prescribed_time": prescribed_time,
            "recommended_reminder_time": prescribed_time,
            "shift_minutes": 0,
            "adherence_rate_pct": 100.0,
            "rationale": "Baseline schedule active. Insufficient delay telemetry."
        }

    n = len(confirmation_delays)
    mean_delay = sum(confirmation_delays) / n
    # Variance
    variance = sum((d - mean_delay) ** 2 for d in confirmation_delays) / n
    std_dev = variance ** 0.5

    # On-time count (within 15 mins of scheduled)
    on_time = sum(1 for d in confirmation_delays if abs(d) <= 15)
    adherence_pct = round((on_time / n) * 100, 1)

    # If consistent habit shift (mean delay >= 25 mins and std dev < 40 mins)
    if mean_delay >= 25 and std_dev < 40:
        base_h, base_m = map(int, prescribed_time.split(":"))
        total_mins = base_h * 60 + base_m + int(mean_delay)
        new_h = (total_mins // 60) % 24
        new_m = total_mins % 60
        adapted_time = f"{new_h:02d}:{new_m:02d}"

        return {
            "is_adapted": True,
            "prescribed_time": prescribed_time,
            "recommended_reminder_time": adapted_time,
            "shift_minutes": int(mean_delay),
            "adherence_rate_pct": adherence_pct,
            "std_deviation_mins": round(std_dev, 1),
            "rationale": f"Consistent average delay of +{int(mean_delay)} mins detected (sigma={round(std_dev, 1)}m). Reminders dynamically shifted from {prescribed_time} to {adapted_time} to synchronize with patient behavioral routine."
        }

    return {
        "is_adapted": False,
        "prescribed_time": prescribed_time,
        "recommended_reminder_time": prescribed_time,
        "shift_minutes": 0,
        "adherence_rate_pct": adherence_pct,
        "std_deviation_mins": round(std_dev, 1),
        "rationale": f"Adherence acceptable ({adherence_pct}%). Fixed schedule maintained."
    }
