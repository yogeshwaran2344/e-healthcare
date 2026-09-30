import random
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..database import get_db
from ..models import User, QueueToken, HospitalWaypoint
from ..auth import get_current_user
from ..ml.navigation_queue_engine import (
    HOSPITAL_WAYPOINTS,
    find_shortest_indoor_route,
    calculate_queue_priority
)

router = APIRouter(prefix="", tags=["Hospital Navigation & Live Queue"])

# ================= NAVIGATION =================

@router.get("/api/navigation/floors")
def get_hospital_navigation_map():
    """
    Returns hospital waypoints and departments organized by floor level.
    """
    floors = {"Ground Floor": [], "1st Floor": [], "2nd Floor": []}
    for code, wp in HOSPITAL_WAYPOINTS.items():
        fl = wp.get("floor", "Ground Floor")
        floors[fl].append({
            "code": code,
            "name": wp["name"],
            "category": wp["category"],
            "x": wp["x"],
            "y": wp["y"],
            "instructions": wp["instructions"]
        })
    return {
        "hospital_name": "Apex Multi-Specialty Hospital & Research Institute",
        "floors": floors,
        "available_destinations": [
            {"code": k, "name": v["name"], "floor": v["floor"], "category": v["category"]}
            for k, v in HOSPITAL_WAYPOINTS.items()
        ]
    }

@router.get("/api/navigation/route")
def get_indoor_navigation_route(
    start: str = Query("ENTRANCE", description="Origin waypoint code"),
    destination: str = Query("OPD_PULMONOLOGY", description="Target department code")
):
    """
    Calculates turn-by-turn indoor routing path and AR camera HUD waypoints.
    """
    route = find_shortest_indoor_route(start, destination)
    return route

# ================= SMART QUEUE =================

@router.get("/api/queue/my-token")
def get_patient_queue_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns patient's active OPD queue token, current token being served,
    queue position, and dynamic wait time estimation.
    """
    token = (
        db.query(QueueToken)
        .filter(QueueToken.patient_id == current_user.id, QueueToken.status.in_(["waiting", "called", "in_consultation"]))
        .order_by(QueueToken.created_at.desc())
        .first()
    )

    if not token:
        # Generate initial realistic demo token
        token_num = f"A-{random.randint(101, 120)}"
        token = QueueToken(
            token_code=token_num,
            patient_id=current_user.id,
            department="OPD Pulmonology & Critical Care",
            priority_level="NORMAL",
            status="waiting",
            queue_number=14,
            estimated_wait_minutes=12
        )
        db.add(token)
        db.commit()
        db.refresh(token)

    # Calculate queue statistics
    serving_number = max(1, token.queue_number - 2)
    serving_code = f"A-{100 + serving_number}"
    patients_ahead = max(0, token.queue_number - serving_number)
    wait_minutes = patients_ahead * 6

    return {
        "token_id": token.id,
        "token_code": token.token_code,
        "department": token.department,
        "priority_level": token.priority_level,
        "status": token.status,
        "your_queue_position": token.queue_number,
        "currently_serving_token": serving_code,
        "patients_ahead": patients_ahead,
        "estimated_wait_minutes": wait_minutes if token.priority_level != "EMERGENCY_CRITICAL" else 0,
        "is_priority_bumped": token.priority_level == "EMERGENCY_CRITICAL"
    }

@router.post("/api/queue/issue-token")
def issue_queue_token(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Issues a new queue token. Patients triaged as Emergency Care or with critical vitals
    are automatically prioritized into EMERGENCY_CRITICAL (P0) at the head of the queue!
    """
    department = payload.get("department", "OPD General Medicine")
    triage_level = payload.get("triage_level", "Doctor Consultation")
    is_iot_critical = payload.get("is_iot_critical", False)

    priority, wait_mins = calculate_queue_priority(triage_level, is_iot_critical)

    prefix = "EMERG" if priority == "EMERGENCY_CRITICAL" else "A"
    code = f"{prefix}-{random.randint(201, 299)}"

    # If priority critical, place at position 1
    queue_pos = 1 if priority == "EMERGENCY_CRITICAL" else random.randint(3, 8)

    token = QueueToken(
        token_code=code,
        patient_id=current_user.id,
        department=department,
        priority_level=priority,
        status="waiting",
        queue_number=queue_pos,
        estimated_wait_minutes=wait_mins
    )
    db.add(token)
    db.commit()
    db.refresh(token)

    return {
        "status": "success",
        "token_code": token.token_code,
        "priority_level": token.priority_level,
        "queue_position": token.queue_number,
        "estimated_wait_minutes": token.estimated_wait_minutes,
        "routing_notice": "EMERGENCY PRIORITY ACTIVATED: Patient automatically routed to immediate triage." if priority == "EMERGENCY_CRITICAL" else "Token registered in regular OPD queue."
    }

@router.get("/api/queue/doctor/live-board")
def get_doctor_queue_board(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns live OPD waiting room queue for clinician dashboard.
    """
    tokens = (
        db.query(QueueToken)
        .order_by(
            QueueToken.priority_level.desc(), # Emergency critical first
            QueueToken.created_at.asc()
        )
        .all()
    )

    board = []
    for t in tokens:
        p = db.query(User).filter(User.id == t.patient_id).first()
        board.append({
            "id": t.id,
            "token_code": t.token_code,
            "patient_name": p.full_name if p else "Patient",
            "patient_age": p.age if p else None,
            "priority_level": t.priority_level,
            "status": t.status,
            "department": t.department,
            "created_at": t.created_at
        })

    return {
        "total_in_queue": len([t for t in board if t["status"] == "waiting"]),
        "active_queue": board
    }

@router.post("/api/queue/call-next/{token_id}")
def call_next_queue_patient(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Doctor marks a queue patient as called / in consultation."""
    t = db.query(QueueToken).filter(QueueToken.id == token_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    t.status = "in_consultation"
    t.called_at = datetime.utcnow()
    db.commit()
    return {"message": f"Patient with Token {t.token_code} called into consultation room."}

@router.post("/api/queue/emergency-bump/{token_id}")
def emergency_bump_patient(
    token_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elevates patient to emergency priority level."""
    t = db.query(QueueToken).filter(QueueToken.id == token_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Token not found")
    t.priority_level = "EMERGENCY_CRITICAL"
    t.queue_number = 1
    t.estimated_wait_minutes = 0
    db.commit()
    return {"message": f"Token {t.token_code} elevated to EMERGENCY_CRITICAL (P0 Bypass)."}
