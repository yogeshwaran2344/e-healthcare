import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, IoTDevice, IoTVitalReading, EmergencyAlert
from ..auth import get_current_user
from ..ml.iot_engine import (
    IOT_DEVICE_CATALOG,
    evaluate_vital_thresholds,
    generate_telemetry_reading,
    generate_ecg_waveform
)

router = APIRouter(prefix="/api/iot", tags=["IoT Wearables & Telemetry"])

@router.get("/devices")
def get_user_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns registered IoT medical wearables for patient. Auto-initializes defaults if new.
    """
    devices = db.query(IoTDevice).filter(IoTDevice.patient_id == current_user.id).all()
    if not devices:
        # Initialize default paired medical devices
        for cat in IOT_DEVICE_CATALOG:
            d = IoTDevice(
                patient_id=current_user.id,
                device_name=cat["device_name"],
                device_type=cat["device_type"],
                device_uid=f"{cat['device_uid']}-{current_user.id}",
                firmware_version=cat["firmware"],
                battery_level=94,
                connection_status="connected",
                last_sync_at=datetime.utcnow()
            )
            db.add(d)
        db.commit()
        devices = db.query(IoTDevice).filter(IoTDevice.patient_id == current_user.id).all()

    return [
        {
            "id": d.id,
            "device_name": d.device_name,
            "device_type": d.device_type,
            "device_uid": d.device_uid,
            "firmware_version": d.firmware_version,
            "battery_level": d.battery_level,
            "connection_status": d.connection_status,
            "last_sync_at": d.last_sync_at
        }
        for d in devices
    ]

from ..consent_service import enforce_patient_consent_or_emergency

@router.get("/vitals/latest")
def get_latest_vitals(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Fetches latest vital telemetry readings (BP, Glucose, SpO2, Heart Rate / ECG, Temperature).
    Doctors can pass patient_id to monitor remote patients with active patient consent or emergency override.
    """
    if patient_id and current_user.role == "doctor" and patient_id != current_user.id:
        enforce_patient_consent_or_emergency(
            db, patient_id, current_user, "vitals", purpose=f"Remote vital telemetry monitoring for patient #{patient_id}"
        )
    target_id = patient_id if (patient_id and current_user.role in ("doctor", "admin")) else current_user.id

    # Retrieve devices for target
    devices = db.query(IoTDevice).filter(IoTDevice.patient_id == target_id).all()
    if not devices and current_user.role == "patient":
        # Trigger init
        get_user_devices(current_user, db)
        devices = db.query(IoTDevice).filter(IoTDevice.patient_id == target_id).all()

    latest_readings = {}
    for d in devices:
        last_r = (
            db.query(IoTVitalReading)
            .filter(IoTVitalReading.device_id == d.id)
            .order_by(IoTVitalReading.recorded_at.desc())
            .first()
        )
        if last_r:
            ecg_pts = json.loads(last_r.ecg_waveform_points) if last_r.ecg_waveform_points else None
            latest_readings[d.device_type] = {
                "reading_id": last_r.id,
                "device_id": d.id,
                "device_name": d.device_name,
                "metric_type": last_r.metric_type,
                "primary_value": last_r.primary_value,
                "secondary_value": last_r.secondary_value,
                "unit": last_r.unit,
                "is_anomaly": last_r.is_anomaly,
                "alert_severity": last_r.alert_severity,
                "alert_message": last_r.alert_message,
                "ecg_waveform": ecg_pts,
                "recorded_at": last_r.recorded_at
            }
        else:
            # Generate initial realistic telemetry baseline
            seed_data = generate_telemetry_reading(d.device_type, simulate_anomaly=False)
            ecg_json = json.dumps(seed_data["ecg_waveform_points"]) if seed_data["ecg_waveform_points"] else None
            new_r = IoTVitalReading(
                patient_id=target_id,
                device_id=d.id,
                metric_type=seed_data["metric_type"],
                primary_value=seed_data["primary_value"],
                secondary_value=seed_data["secondary_value"],
                unit=seed_data["unit"],
                is_anomaly=seed_data["is_anomaly"],
                alert_severity=seed_data["alert_severity"],
                alert_message=seed_data["alert_message"],
                ecg_waveform_points=ecg_json,
                recorded_at=datetime.utcnow()
            )
            db.add(new_r)
            db.commit()
            db.refresh(new_r)
            latest_readings[d.device_type] = {
                "reading_id": new_r.id,
                "device_id": d.id,
                "device_name": d.device_name,
                "metric_type": new_r.metric_type,
                "primary_value": new_r.primary_value,
                "secondary_value": new_r.secondary_value,
                "unit": new_r.unit,
                "is_anomaly": new_r.is_anomaly,
                "alert_severity": new_r.alert_severity,
                "alert_message": new_r.alert_message,
                "ecg_waveform": seed_data["ecg_waveform_points"],
                "recorded_at": new_r.recorded_at
            }

    # Check if there is any active critical alert
    has_critical = any(v.get("alert_severity") == "CRITICAL" for v in latest_readings.values())

    return {
        "patient_id": target_id,
        "telemetry_stream": latest_readings,
        "has_critical_emergency": has_critical,
        "synced_at": datetime.utcnow().isoformat()
    }

@router.post("/simulate-stream")
def simulate_iot_stream(
    device_type: str = Query(..., description="bp_monitor, glucose_sensor, ecg_sensor, pulse_oximeter"),
    trigger_emergency: bool = Query(False, description="Set true to inject critical threshold breach"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Simulation endpoint that allows streaming live telemetry data from connected wearables.
    Supports injecting emergency thresholds to test real-time ER alerts.
    """
    device = (
        db.query(IoTDevice)
        .filter(IoTDevice.patient_id == current_user.id, IoTDevice.device_type == device_type)
        .first()
    )
    if not device:
        # Fallback to any device
        device = db.query(IoTDevice).filter(IoTDevice.patient_id == current_user.id).first()
        if not device:
            raise HTTPException(status_code=404, detail="No IoT device found for user")

    synth = generate_telemetry_reading(device_type, simulate_anomaly=trigger_emergency)
    ecg_json = json.dumps(synth["ecg_waveform_points"]) if synth["ecg_waveform_points"] else None

    reading = IoTVitalReading(
        patient_id=current_user.id,
        device_id=device.id,
        metric_type=synth["metric_type"],
        primary_value=synth["primary_value"],
        secondary_value=synth["secondary_value"],
        unit=synth["unit"],
        is_anomaly=synth["is_anomaly"],
        alert_severity=synth["alert_severity"],
        alert_message=synth["alert_message"],
        ecg_waveform_points=ecg_json,
        recorded_at=datetime.utcnow()
    )
    device.last_sync_at = datetime.utcnow()
    db.add(reading)
    db.commit()
    db.refresh(reading)

    return {
        "status": "success",
        "device_name": device.device_name,
        "metric_type": reading.metric_type,
        "primary_value": reading.primary_value,
        "secondary_value": reading.secondary_value,
        "unit": reading.unit,
        "alert_severity": reading.alert_severity,
        "alert_message": reading.alert_message,
        "is_critical": reading.alert_severity == "CRITICAL",
        "ecg_points": synth["ecg_waveform_points"]
    }
