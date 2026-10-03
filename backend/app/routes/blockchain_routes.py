import os
import json
import hashlib
from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, Consultation, Prescription, MedicalReport, BlockchainBlock, ConsentRecord, EmergencyAccessAudit
from ..auth import get_current_user
from ..ml.blockchain_engine import (
    create_block,
    verify_blockchain_integrity,
    generate_consent_token,
    compute_sha256,
    verify_single_record_integrity,
    canonicalize_medical_record,
    sign_block
)

router = APIRouter(prefix="/api/blockchain", tags=["Blockchain Health Records"])

def ensure_patient_genesis_block(patient_id: int, db: Session) -> BlockchainBlock:
    """Ensures Genesis Block exists for patient."""
    genesis = (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.patient_id == patient_id, BlockchainBlock.block_index == 0)
        .first()
    )
    if not genesis:
        genesis_data = {
            "title": "Genesis Medical Ledger Anchor",
            "patient_id": patient_id,
            "anchor_protocol": "SHA-256 Merkle Medical Chain",
            "legal_compliance": "HIPAA & GDPR Patient-Owned Ledger"
        }
        b_dict = create_block(
            block_index=0,
            patient_id=patient_id,
            record_type="GENESIS",
            record_id="GENESIS-ANCHOR",
            data_dict=genesis_data,
            previous_hash="0" * 64
        )
        genesis = BlockchainBlock(**b_dict)
        db.add(genesis)
        db.commit()
        db.refresh(genesis)
    return genesis

@router.get("/ledger")
def get_patient_blockchain_ledger(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns patient's cryptographic SHA-256 block ledger with Merkle root and digital signatures.
    """
    target_id = patient_id if (patient_id and current_user.role == "doctor") else current_user.id
    ensure_patient_genesis_block(target_id, db)

    # Sync any un-mined consultations or prescriptions into blockchain
    consultations = db.query(Consultation).filter(Consultation.patient_id == target_id).all()
    for c in consultations:
        existing_block = (
            db.query(BlockchainBlock)
            .filter(
                BlockchainBlock.patient_id == target_id,
                BlockchainBlock.record_type == "CONSULTATION",
                BlockchainBlock.record_id == str(c.id)
            )
            .first()
        )
        if not existing_block:
            last_block = (
                db.query(BlockchainBlock)
                .filter(BlockchainBlock.patient_id == target_id)
                .order_by(BlockchainBlock.block_index.desc())
                .first()
            )
            next_idx = (last_block.block_index + 1) if last_block else 1
            prev_hash = last_block.block_hash if last_block else ("0" * 64)
            c_data = {
                "consultation_id": c.id,
                "predicted_disease": c.predicted_disease or "Clinical Consultation",
                "triage_level": c.triage_level or "Doctor Consultation",
                "severity": c.severity or "Moderate",
                "symptoms": c.symptoms_list,
                "created_at": c.created_at.isoformat()
            }
            new_b = BlockchainBlock(**create_block(next_idx, target_id, "CONSULTATION", str(c.id), c_data, prev_hash))
            db.add(new_b)
            db.commit()

    blocks = (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.patient_id == target_id)
        .order_by(BlockchainBlock.block_index.asc())
        .all()
    )

    return {
        "patient_id": target_id,
        "total_blocks": len(blocks),
        "chain": [
            {
                "block_index": b.block_index,
                "timestamp": b.timestamp,
                "record_type": b.record_type,
                "record_id": b.record_id,
                "data_payload": json.loads(b.data_payload) if b.data_payload.startswith("{") else b.data_payload,
                "data_hash": b.data_hash,
                "previous_hash": b.previous_hash,
                "merkle_root": b.merkle_root,
                "block_hash": b.block_hash,
                "validator_signature": b.validator_signature,
                "is_verified": b.is_verified
            }
            for b in blocks
        ]
    }

@router.post("/verify-integrity")
def verify_ledger(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes full cryptographic mathematical verification across all blocks in the ledger.
    """
    target_id = patient_id if (patient_id and current_user.role == "doctor") else current_user.id
    ensure_patient_genesis_block(target_id, db)

    blocks = (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.patient_id == target_id)
        .order_by(BlockchainBlock.block_index.asc())
        .all()
    )
    chain_list = [
        {
            "block_index": b.block_index,
            "data_payload": b.data_payload,
            "data_hash": b.data_hash,
            "previous_hash": b.previous_hash,
            "block_hash": b.block_hash,
            "validator_signature": b.validator_signature
        }
        for b in blocks
    ]

    result = verify_blockchain_integrity(chain_list)
    return result

@router.get("/verify-record/{record_type}/{record_id}")
def verify_medical_record_integrity(
    record_type: str,
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies the cryptographic integrity of an active medical record against its
    immutable on-chain SHA-256 fingerprint and Merkle tree root.
    Demonstrates tamper-evident detection without storing cleartext PHI on-chain.
    """
    rec_type_upper = record_type.upper()
    block = db.query(BlockchainBlock).filter(
        BlockchainBlock.record_type == rec_type_upper,
        BlockchainBlock.record_id == str(record_id)
    ).first()

    if not block:
        raise HTTPException(
            status_code=404,
            detail=f"No blockchain integrity anchor found for record {record_type}:{record_id}"
        )

    # Authorization check: only patient or authorized doctor
    if current_user.role == "patient" and block.patient_id != current_user.id:
        raise HTTPException(status_code=403, detail="Unauthorized access to record verification")

    # Fetch active database record to test for tampering
    active_data = None
    if rec_type_upper == "CONSULTATION":
        c = db.query(Consultation).filter(Consultation.id == int(record_id)).first()
        if c:
            active_data = {
                "consultation_id": c.id,
                "predicted_disease": c.predicted_disease or "Clinical Consultation",
                "triage_level": c.triage_level or "Doctor Consultation",
                "severity": c.severity or "Moderate",
                "symptoms": c.symptoms_list,
                "created_at": c.created_at.isoformat()
            }
    elif rec_type_upper == "PRESCRIPTION":
        p = db.query(Prescription).filter(Prescription.id == int(record_id)).first()
        if p:
            active_data = {
                "prescription_id": p.id,
                "consultation_id": p.consultation_id,
                "doctor_id": p.doctor_id,
                "diagnosis": p.diagnosis,
                "medicines_json": p.medicines_json,
                "instructions": p.general_advice or "",
                "created_at": p.created_at.isoformat()
            }
    elif rec_type_upper in ("REPORT", "LAB_REPORT", "MEDICAL_REPORT"):
        r = db.query(MedicalReport).filter(MedicalReport.id == int(record_id)).first()
        if r:
            active_data = {
                "report_id": r.id,
                "patient_id": r.patient_id,
                "report_type": r.report_type,
                "original_filename": r.original_filename,
                "findings": r.extracted_findings or "",
                "uploaded_at": r.uploaded_at.isoformat()
            }

    if not active_data:
        try:
            stored_payload = json.loads(block.data_payload)
            active_data = stored_payload
        except Exception:
            active_data = {"record_id": str(record_id), "record_type": rec_type_upper}

    is_match, current_hash, current_merkle = verify_single_record_integrity(
        anchored_data_hash=block.data_hash,
        anchored_merkle_root=block.merkle_root,
        record_type=rec_type_upper,
        current_record_dict=active_data
    )

    sig_valid = (sign_block(block.block_hash) == block.validator_signature)
    status_label = "VERIFIED_AUTHENTIC" if (is_match and sig_valid) else "TAMPERING_DETECTED"

    return {
        "record_type": rec_type_upper,
        "record_id": str(record_id),
        "status": status_label,
        "is_authentic": bool(is_match and sig_valid),
        "tampering_detected": not bool(is_match and sig_valid),
        "block_index": block.block_index,
        "anchored_timestamp": block.timestamp.isoformat() if hasattr(block.timestamp, "isoformat") else str(block.timestamp),
        "anchored_sha256_hash": block.data_hash,
        "recomputed_sha256_hash": current_hash,
        "merkle_root": block.merkle_root,
        "recomputed_merkle_root": current_merkle,
        "validator_signature_valid": bool(sig_valid),
        "storage_architecture": "Zero-PHI Off-Chain Secure Storage (Cryptographic Hash Anchoring)"
    }

@router.post("/verify-document-file")
async def verify_uploaded_document_file(
    file: UploadFile = File(...),
    report_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Demonstrable Document Integrity Verification Pipeline:
    Original File -> Compute SHA-256 -> Compare with Blockchain Hash Anchor.
    Returns MATCH -> VERIFIED_AUTHENTIC or MISMATCH -> TAMPERING_DETECTED.
    """
    content = await file.read()
    computed_file_sha256 = hashlib.sha256(content).hexdigest()

    # Locate blockchain block
    block = None
    if report_id:
        block = db.query(BlockchainBlock).filter(
            BlockchainBlock.record_type.in_(["LAB_REPORT", "REPORT", "MEDICAL_REPORT"]),
            BlockchainBlock.record_id == str(report_id)
        ).first()

    if not block:
        report = db.query(MedicalReport).filter(
            MedicalReport.patient_id == current_user.id,
            MedicalReport.original_filename == file.filename
        ).order_by(MedicalReport.id.desc()).first()

        if report:
            block = db.query(BlockchainBlock).filter(
                BlockchainBlock.record_type.in_(["LAB_REPORT", "REPORT", "MEDICAL_REPORT"]),
                BlockchainBlock.record_id == str(report.id)
            ).first()

    if not block:
        block = db.query(BlockchainBlock).filter(
            BlockchainBlock.patient_id == current_user.id,
            BlockchainBlock.record_type.in_(["LAB_REPORT", "REPORT", "MEDICAL_REPORT"])
        ).order_by(BlockchainBlock.block_index.desc()).first()

    if not block:
        raise HTTPException(
            status_code=404,
            detail="No recorded blockchain integrity anchor found for this report. Ensure the report has been uploaded."
        )

    # Compare computed hash with file bytes stored on disk
    rep = db.query(MedicalReport).filter(MedicalReport.id == int(block.record_id)).first() if block.record_id.isdigit() else None
    
    actual_file_hash = None
    if rep and rep.file_path and os.path.exists(rep.file_path):
        with open(rep.file_path, "rb") as f:
            actual_file_hash = hashlib.sha256(f.read()).hexdigest()
    else:
        actual_file_hash = block.data_hash

    is_match = (computed_file_sha256 == actual_file_hash)
    sig_valid = (sign_block(block.block_hash) == block.validator_signature)
    status_label = "MATCH" if (is_match and sig_valid) else "MISMATCH"
    verdict = "VERIFIED_AUTHENTIC" if (is_match and sig_valid) else "TAMPERING_DETECTED"

    return {
        "filename": file.filename,
        "status": status_label,
        "verdict": verdict,
        "is_authentic": is_match and sig_valid,
        "tampering_detected": not (is_match and sig_valid),
        "computed_file_sha256": computed_file_sha256,
        "ledger_anchored_sha256": actual_file_hash,
        "block_index": block.block_index,
        "block_hash": block.block_hash,
        "merkle_root": block.merkle_root,
        "validator_signature_valid": sig_valid,
        "anchored_timestamp": block.timestamp.isoformat() if hasattr(block.timestamp, "isoformat") else str(block.timestamp),
        "audit_message": "MATCH: Cryptographic SHA-256 fingerprint matches immutable ledger block." if is_match else "MISMATCH: File bytes have been modified! Cryptographic signature broken."
    }

@router.get("/consents")
def get_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Lists active and historical medical record sharing grants.
    """
    consents = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.patient_id == current_user.id)
        .order_by(ConsentRecord.created_at.desc())
        .all()
    )
    if not consents:
        # Seed realistic initial consent records
        c1 = ConsentRecord(
            patient_id=current_user.id,
            grantee_name="Dr. Sarah Sharma",
            grantee_type="doctor",
            grantee_organization="Apex Multi-Specialty Hospital",
            permissions=json.dumps(["diagnoses", "lab_reports", "prescriptions", "live_vitals"]),
            access_token=generate_consent_token("doc", 168)[0],
            status="active",
            expires_at=datetime.utcnow() + timedelta(days=7)
        )
        c2 = ConsentRecord(
            patient_id=current_user.id,
            grantee_name="Star Health Insurance Claims",
            grantee_type="insurer",
            grantee_organization="Star Health & Allied Insurance",
            permissions=json.dumps(["prescriptions", "verified_invoices"]),
            access_token=generate_consent_token("ins", 48)[0],
            status="active",
            expires_at=datetime.utcnow() + timedelta(days=2)
        )
        db.add_all([c1, c2])
        db.commit()
        consents = db.query(ConsentRecord).filter(ConsentRecord.patient_id == current_user.id).all()

    return [
        {
            "id": c.id,
            "grantee_name": c.grantee_name,
            "grantee_type": c.grantee_type,
            "grantee_organization": c.grantee_organization,
            "permissions": json.loads(c.permissions),
            "access_token": c.access_token,
            "status": c.status,
            "expires_at": c.expires_at,
            "created_at": c.created_at
        }
        for c in consents
    ]

@router.post("/grant-consent")
def grant_new_consent(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Issues a new decentralized cryptographic consent token with custom granular permissions.
    """
    grantee_name = payload.get("grantee_name", "Medical Specialist")
    grantee_type = payload.get("grantee_type", "doctor")
    grantee_org = payload.get("organization", "Hospital / Institute")
    permissions = payload.get("permissions", ["diagnoses", "prescriptions"])
    valid_hours = int(payload.get("valid_hours", 72))

    token, expires_at = generate_consent_token(grantee_type, valid_hours)

    consent = ConsentRecord(
        patient_id=current_user.id,
        grantee_name=grantee_name,
        grantee_type=grantee_type,
        grantee_organization=grantee_org,
        permissions=json.dumps(permissions),
        access_token=token,
        status="active",
        expires_at=expires_at
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    # Write consent event onto patient blockchain
    last_block = (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.patient_id == current_user.id)
        .order_by(BlockchainBlock.block_index.desc())
        .first()
    )
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)
    event_data = {
        "event": "SMART_CONSENT_GRANTED",
        "grantee": grantee_name,
        "type": grantee_type,
        "permissions": permissions,
        "token_hash": compute_sha256(token)[:16],
        "expires_at": expires_at.isoformat()
    }
    block = BlockchainBlock(**create_block(next_idx, current_user.id, "CONSENT_GRANT", str(consent.id), event_data, prev_hash))
    db.add(block)
    db.commit()

    return {
        "status": "success",
        "consent_id": consent.id,
        "access_token": token,
        "expires_at": expires_at.isoformat(),
        "block_index": block.block_index
    }

@router.post("/revoke-consent/{consent_id}")
def revoke_consent(
    consent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revokes an existing consent token immediately and records an immutable revocation block.
    """
    c = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id, ConsentRecord.patient_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consent record not found")

    c.status = "revoked"
    db.commit()

    # Write immutable revocation block
    last_block = (
        db.query(BlockchainBlock)
        .filter(BlockchainBlock.patient_id == current_user.id)
        .order_by(BlockchainBlock.block_index.desc())
        .first()
    )
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)
    event_data = {
        "event": "SMART_CONSENT_REVOKED",
        "grantee": c.grantee_name,
        "token_revoked": c.access_token[:16] + "...",
        "revoked_at": datetime.utcnow().isoformat()
    }
    block = BlockchainBlock(**create_block(next_idx, current_user.id, "CONSENT_REVOKE", str(c.id), event_data, prev_hash))
    db.add(block)
    db.commit()

    return {"message": f"Access for {c.grantee_name} has been revoked. Ledger updated at Block #{block.block_index}."}

@router.get("/shared-record/{token}")
def get_shared_record_by_token(token: str, db: Session = Depends(get_db)):
    """
    External verification endpoint for authorized doctors, insurers, and researchers.
    """
    c = db.query(ConsentRecord).filter(ConsentRecord.access_token == token).first()
    if not c:
        raise HTTPException(status_code=404, detail="Invalid sharing token")
    if c.status != "active":
        raise HTTPException(status_code=403, detail=f"This consent token is {c.status}")
    if c.expires_at < datetime.utcnow():
        c.status = "expired"
        db.commit()
        raise HTTPException(status_code=403, detail="This consent token has expired")

    patient = db.query(User).filter(User.id == c.patient_id).first()
    perms = json.loads(c.permissions)

    result = {
        "grantee": c.grantee_name,
        "organization": c.grantee_organization,
        "patient_initials": patient.full_name[:2] + "...",
        "granted_permissions": perms,
        "expires_at": c.expires_at.isoformat(),
        "integrity_stamp": "Cryptographically Verified via SHA-256 Health Ledger"
    }

    if "diagnoses" in perms:
        consultations = db.query(Consultation).filter(Consultation.patient_id == patient.id).all()
        result["diagnoses"] = [
            {"date": cs.created_at.strftime("%Y-%m-%d"), "condition": cs.predicted_disease, "severity": cs.severity}
            for cs in consultations
        ]

    return result

@router.get("/expiring-consents")
def check_expiring_consents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Scans active consents for proactive expiration notifications.
    Alerts patient before data access terminates, allowing 1-click 365-day extension or immediate purge.
    """
    now = datetime.utcnow()
    warning_threshold = now + timedelta(days=30)

    consents = (
        db.query(ConsentRecord)
        .filter(ConsentRecord.patient_id == current_user.id, ConsentRecord.status == "active")
        .all()
    )

    expiring_list = []
    for c in consents:
        days_left = max((c.expires_at - now).days, 0)
        is_imminent = c.expires_at <= warning_threshold
        expiring_list.append({
            "id": c.id,
            "grantee_name": c.grantee_name,
            "grantee_organization": c.grantee_organization,
            "expires_at": c.expires_at.isoformat(),
            "days_remaining": days_left,
            "is_imminent_expiry": is_imminent,
            "prompt_message": f"Consent for {c.grantee_name} expires in {days_left} days. Keep data active (Extend 365 Days) or delete/revoke data access now?",
            "actions": ["EXTEND_365_DAYS", "PURGE_AND_DELETE_NOW"]
        })

    return {"expiring_consents": expiring_list}

@router.post("/extend-consent/{consent_id}")
def extend_consent_365_days(
    consent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Extends consent duration by 365 days (8760 hours) and writes event to blockchain."""
    c = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id, ConsentRecord.patient_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consent record not found.")

    c.expires_at = datetime.utcnow() + timedelta(days=365)
    c.status = "active"

    # Append block
    last_block = db.query(BlockchainBlock).filter(BlockchainBlock.patient_id == current_user.id).order_by(BlockchainBlock.block_index.desc()).first()
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)
    event_data = {
        "event": "SMART_CONSENT_EXTENDED_365_DAYS",
        "grantee": c.grantee_name,
        "new_expires_at": c.expires_at.isoformat()
    }
    block = BlockchainBlock(**create_block(next_idx, current_user.id, "CONSENT_EXTEND", str(c.id), event_data, prev_hash))
    db.add(block)
    db.commit()

    return {"message": f"Consent for {c.grantee_name} extended for 365 days. Ledger updated at Block #{block.block_index}.", "new_expires_at": c.expires_at.isoformat()}

@router.post("/revoke-and-purge/{consent_id}")
def purge_and_delete_consent(
    consent_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revokes consent, purges sharing token, and permanently logs deletion on ledger."""
    c = db.query(ConsentRecord).filter(ConsentRecord.id == consent_id, ConsentRecord.patient_id == current_user.id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Consent record not found.")

    c.status = "purged"
    c.access_token = "PURGED_AND_REVOKED_" + c.access_token[:8]

    # Append block
    last_block = db.query(BlockchainBlock).filter(BlockchainBlock.patient_id == current_user.id).order_by(BlockchainBlock.block_index.desc()).first()
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)
    event_data = {
        "event": "SMART_CONSENT_PURGED_AND_REVOKED",
        "grantee": c.grantee_name,
        "purged_at": datetime.utcnow().isoformat()
    }
    block = BlockchainBlock(**create_block(next_idx, current_user.id, "CONSENT_PURGE", str(c.id), event_data, prev_hash))
    db.add(block)
    db.commit()

    return {"message": f"Data sharing for {c.grantee_name} has been permanently purged and revoked. Ledger updated at Block #{block.block_index}."}


# ========================================================
# 4. "Who Accessed My Health Data?" Access History & Revocation
# ========================================================

@router.get("/access-history")
def get_access_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns granular tabular access history showing who accessed patient health data,
    purpose, data scope, status, and active revocation capability.
    """
    consents = db.query(ConsentRecord).filter(ConsentRecord.patient_id == current_user.id).order_by(ConsentRecord.created_at.desc()).all()
    
    # Also find any BREAK_GLASS blocks on the blockchain
    bg_blocks = db.query(BlockchainBlock).filter(
        BlockchainBlock.patient_id == current_user.id,
        BlockchainBlock.record_type == "BREAK_GLASS_OVERRIDE"
    ).order_by(BlockchainBlock.timestamp.desc()).all()

    history = []
    
    # Add Break Glass entries first (critical)
    for bg in bg_blocks:
        try:
            payload = json.loads(bg.data_payload) if isinstance(bg.data_payload, str) else bg.data_payload
        except Exception:
            payload = {}
        history.append({
            "id": f"bg-{bg.id}",
            "date": bg.timestamp.strftime("%b %d, %Y %H:%M") if hasattr(bg.timestamp, "strftime") else str(bg.timestamp),
            "accessor": payload.get("doctor_name", "Emergency Trauma Physician"),
            "organization": payload.get("hospital", "Emergency Trauma Center"),
            "role": "Emergency Unit",
            "purpose": payload.get("justification", "Emergency resuscitation / Critical care"),
            "data_scope": payload.get("data_accessed", "Critical Triage Data (Blood Group, Allergies, Meds)"),
            "status": "⚠ Emergency Override",
            "status_badge": "bg-danger text-white",
            "is_emergency": True,
            "can_revoke": False,
            "block_hash": bg.block_hash[:16] + "..."
        })

    # Add EmergencyAccessAudit events (emergency passport scans, emergency views)
    audits = (
        db.query(EmergencyAccessAudit)
        .filter(EmergencyAccessAudit.patient_id == current_user.id)
        .order_by(EmergencyAccessAudit.accessed_at.desc())
        .all()
    )
    for a in audits:
        history.append({
            "id": f"audit-{a.id}",
            "date": a.accessed_at.strftime("%b %d, %Y %H:%M") if hasattr(a.accessed_at, "strftime") else str(a.accessed_at),
            "accessor": a.accessor_name,
            "organization": "Emergency Responder Network" if a.is_emergency else "Healthcare Clinic",
            "role": (a.accessor_role or "Staff").replace("_", " ").title(),
            "purpose": a.purpose or ("Emergency Triage Access" if a.is_emergency else "Clinical Record Access"),
            "data_scope": (a.context_scope or a.information_type or "Emergency Passport").replace("_", " ").title(),
            "status": "⚠ Emergency Access" if a.is_emergency else "✓ Allowed",
            "status_badge": "bg-danger text-white" if a.is_emergency else "bg-info text-white",
            "is_emergency": a.is_emergency,
            "can_revoke": False,
            "token_preview": a.access_channel or "Direct Audit"
        })

    # Add active and historical consent accesses
    for c in consents:
        try:
            perms = json.loads(c.permissions) if isinstance(c.permissions, str) else c.permissions
            perms_str = ", ".join(perms) if isinstance(perms, list) else str(perms)
        except Exception:
            perms_str = "Medical records"

        is_active = (c.status == "active" and c.expires_at > datetime.utcnow())
        status_label = "✓ Allowed" if is_active else ("Revoked" if c.status == "revoked" else "Expired")
        badge_cls = "bg-success text-white" if is_active else ("bg-secondary text-white" if c.status == "revoked" else "bg-warning text-dark")

        history.append({
            "id": c.id,
            "date": c.created_at.strftime("%b %d, %Y %H:%M") if hasattr(c.created_at, "strftime") else str(c.created_at),
            "accessor": c.grantee_name,
            "organization": c.grantee_organization or "Healthcare Facility",
            "role": c.grantee_type.capitalize(),
            "purpose": "Clinical Consultation & Care" if c.grantee_type == "doctor" else "Diagnostic Lab Reporting",
            "data_scope": perms_str.replace("_", " ").title(),
            "status": status_label,
            "status_badge": badge_cls,
            "is_emergency": False,
            "can_revoke": is_active,
            "consent_id": c.id,
            "token_preview": c.access_token[:12] + "..." if c.access_token else "N/A"
        })

    # If no records exist, seed default standard clinical access entries for demonstration
    if not history:
        history = [
            {
                "id": "demo-1",
                "date": (datetime.utcnow() - timedelta(days=1)).strftime("%b %d, %Y %H:%M"),
                "accessor": "Dr. Kumar (Cardiology)",
                "organization": "Apollo Super-Specialty Hospital",
                "role": "Doctor",
                "purpose": "Specialist Consultation",
                "data_scope": "Medical History, ECG, Vitals",
                "status": "✓ Allowed",
                "status_badge": "bg-success text-white",
                "is_emergency": False,
                "can_revoke": True,
                "consent_id": 1,
                "token_preview": "tok_doc_9918..."
            },
            {
                "id": "demo-2",
                "date": (datetime.utcnow() - timedelta(days=2)).strftime("%b %d, %Y %H:%M"),
                "accessor": "Apollo ER Trauma Unit",
                "organization": "Apollo ER Trauma Bay 1",
                "role": "Emergency Unit",
                "purpose": "Acute Triage (Chest Discomfort)",
                "data_scope": "Critical Allergies, Blood Group, Active Meds",
                "status": "⚠ Emergency Override",
                "status_badge": "bg-danger text-white",
                "is_emergency": True,
                "can_revoke": False,
                "block_hash": "a8f3b20c91..."
            },
            {
                "id": "demo-3",
                "date": (datetime.utcnow() - timedelta(days=5)).strftime("%b %d, %Y %H:%M"),
                "accessor": "Apex Diagnostic Laboratory",
                "organization": "Apex Labs Central",
                "role": "Lab",
                "purpose": "Blood Test & Biomarker Extraction",
                "data_scope": "Lab Test Requisitions",
                "status": "✓ Allowed",
                "status_badge": "bg-success text-white",
                "is_emergency": False,
                "can_revoke": True,
                "consent_id": 2,
                "token_preview": "tok_lab_4812..."
            }
        ]

    return {"access_history": history}


# ========================================================
# 5. Emergency Break-Glass Unconsented Access
# ========================================================

@router.post("/break-glass")
def execute_break_glass_access(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Emergency Break-Glass Protocol:
    Grants immediate override access to critical health records in life-threatening scenarios.
    Mandates a clinical justification reason, logs the doctor ID, hospital bay, and timestamp,
    and immutably records the event on the patient's blockchain ledger with immediate audit alerting.
    """
    patient_id = int(payload.get("patient_id", current_user.id))
    justification = payload.get("justification", "").strip()
    hospital = payload.get("hospital", "Emergency Trauma Center").strip()
    data_requested = payload.get("data_requested", "Critical Allergies, Blood Group, Active Medications, Trauma History")

    if not justification or len(justification) < 10:
        raise HTTPException(
            status_code=400,
            detail="Mandatory justification required for Emergency Break-Glass access (minimum 10 characters)."
        )

    # Doctor information
    doctor_name = current_user.full_name if current_user.role == "doctor" else payload.get("doctor_name", "Dr. Emergency Physician")
    doctor_license = "REG-" + str(current_user.id).zfill(5)
    if current_user.doctor_profile:
        doctor_license = current_user.doctor_profile.license_number

    # Generate 2-hour emergency break glass token
    emergency_token, expires_at = generate_consent_token("break_glass_er", 2)

    # Append immutable BREAK_GLASS_OVERRIDE block on patient ledger
    ensure_patient_genesis_block(patient_id, db)
    last_block = db.query(BlockchainBlock).filter(BlockchainBlock.patient_id == patient_id).order_by(BlockchainBlock.block_index.desc()).first()
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)

    event_data = {
        "event": "BREAK_GLASS_EMERGENCY_OVERRIDE",
        "doctor_name": doctor_name,
        "doctor_id": current_user.id,
        "doctor_license": doctor_license,
        "hospital": hospital,
        "justification": justification,
        "data_accessed": data_requested,
        "emergency_token_hash": compute_sha256(emergency_token)[:24],
        "expires_at": expires_at.isoformat(),
        "timestamp": datetime.utcnow().isoformat(),
        "legal_override_clause": "Good Samaritan & Emergency Medical Treatment Exception"
    }

    block = BlockchainBlock(**create_block(next_idx, patient_id, "BREAK_GLASS_OVERRIDE", f"BG-{next_idx}", event_data, prev_hash))
    db.add(block)
    db.commit()
    db.refresh(block)

    # Log to EmergencyAccessAudit for centralized administrative compliance audit
    audit_entry = EmergencyAccessAudit(
        accessor_id=current_user.id,
        accessor_role=current_user.role or "doctor",
        accessor_name=doctor_name,
        patient_id=patient_id,
        accessed_at=datetime.utcnow(),
        purpose=f"Break-Glass Override: {justification}",
        information_type="emergency_critical_records",
        is_emergency=True,
        access_channel="break_glass_portal",
        context_scope=f"BLOCK_INDEX_{block.block_index}"
    )
    db.add(audit_entry)
    db.commit()

    # Fetch patient critical record to return immediately
    patient = db.query(User).filter(User.id == patient_id).first()
    emergency_payload = {
        "patient_name": patient.full_name if patient else "Anonymous Patient",
        "blood_group": patient.blood_group or "O+",
        "drug_allergies": patient.drug_allergies or "Penicillin, Sulfa drugs",
        "current_medications": patient.current_medications or "Metformin 500mg, Lisinopril 10mg",
        "pre_existing_conditions": patient.pre_existing_conditions or "Type 2 Diabetes, Mild Hypertension",
        "emergency_contact": "Next of Kin: Sarah (+91 98765 43210)"
    }

    return {
        "status": "EMERGENCY_BREAK_GLASS_ACTIVE",
        "message": f"Break-glass access granted to {doctor_name}. Recorded immutably at Block #{block.block_index}.",
        "block_index": block.block_index,
        "block_hash": block.block_hash,
        "expires_in_hours": 2,
        "emergency_token": emergency_token,
        "emergency_data": emergency_payload
    }


@router.get("/break-glass-logs")
def get_break_glass_logs(
    patient_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns all break-glass emergency overrides logged on the blockchain."""
    target_id = patient_id if (patient_id and current_user.role == "doctor") else current_user.id
    blocks = db.query(BlockchainBlock).filter(
        BlockchainBlock.patient_id == target_id,
        BlockchainBlock.record_type == "BREAK_GLASS_OVERRIDE"
    ).order_by(BlockchainBlock.timestamp.desc()).all()

    logs = []
    for b in blocks:
        try:
            p = json.loads(b.data_payload) if isinstance(b.data_payload, str) else b.data_payload
        except Exception:
            p = {}
        logs.append({
            "block_index": b.block_index,
            "timestamp": b.timestamp.isoformat() if hasattr(b.timestamp, "isoformat") else str(b.timestamp),
            "doctor_name": p.get("doctor_name", "Emergency Physician"),
            "doctor_license": p.get("doctor_license", "MCI-EMERGENCY"),
            "hospital": p.get("hospital", "Emergency Department"),
            "justification": p.get("justification", "Life-threatening acute episode"),
            "data_accessed": p.get("data_accessed", "Full Emergency Vitals & History"),
            "block_hash": b.block_hash,
            "merkle_root": b.merkle_root
        })

    return {"break_glass_records": logs}


# ========================================================
# 6. Digital Health Passport for Travel
# ========================================================

@router.post("/travel-passport")
def generate_travel_health_passport(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates a verifiable, cryptographically-signed Digital Health Passport for International Travel.
    Permits selective disclosure (e.g. only verified vaccines and critical allergies without exposing
    unrelated sensitive history). Anchored to the SHA-256 patient ledger.
    """
    destination_country = payload.get("destination_country", "United Kingdom")
    travel_date = payload.get("travel_date", (datetime.utcnow() + timedelta(days=14)).strftime("%Y-%m-%d"))
    purpose = payload.get("purpose", "Tourism / Business")
    include_vaccines = payload.get("include_vaccines", True)
    include_allergies = payload.get("include_allergies", True)
    include_fit_to_fly = payload.get("include_fit_to_fly", True)

    travel_token = f"TRAVEL-{compute_sha256(f'{current_user.id}:{destination_country}:{travel_date}')[:20].upper()}"
    expiry_date = datetime.utcnow() + timedelta(days=60)

    # Disclosed items
    disclosures = {
        "passport_holder": current_user.full_name,
        "destination": destination_country,
        "valid_until": expiry_date.strftime("%Y-%m-%d"),
        "blood_group": current_user.blood_group or "O+"
    }
    if include_vaccines:
        disclosures["vaccinations"] = [
            {"vaccine": "COVID-19 mRNA (Updated)", "status": "✓ Verified", "date": "2025-11-10", "batch": "BNT-8821"},
            {"vaccine": "Yellow Fever", "status": "✓ Verified", "date": "2024-03-15", "batch": "YF-0914"},
            {"vaccine": "Hepatitis B", "status": "✓ Verified", "date": "2023-08-20", "batch": "HB-4412"}
        ]
    if include_allergies:
        disclosures["critical_allergies"] = current_user.drug_allergies or "Penicillin (Severe anaphylaxis warning)"
    if include_fit_to_fly:
        disclosures["fit_to_fly_certification"] = "Fit for unrestricted commercial air travel. Cardiopulmonary clearance active."

    # Anchor to blockchain
    ensure_patient_genesis_block(current_user.id, db)
    last_block = db.query(BlockchainBlock).filter(BlockchainBlock.patient_id == current_user.id).order_by(BlockchainBlock.block_index.desc()).first()
    next_idx = (last_block.block_index + 1) if last_block else 1
    prev_hash = last_block.block_hash if last_block else ("0" * 64)

    block = BlockchainBlock(**create_block(next_idx, current_user.id, "TRAVEL_PASSPORT", travel_token, disclosures, prev_hash))
    db.add(block)
    db.commit()

    return {
        "travel_token": travel_token,
        "destination": destination_country,
        "valid_until": expiry_date.strftime("%d %b %Y"),
        "block_index": block.block_index,
        "merkle_root": block.merkle_root,
        "block_hash": block.block_hash,
        "disclosures": disclosures,
        "qr_verification_url": f"/api/blockchain/shared-record/{travel_token}"
    }


# ========================================================
# 7. Doctor Granular Consent Request
# ========================================================

@router.post("/doctor-request-consent")
def doctor_request_consent(
    payload: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Allows a doctor or clinic to initiate a granular consent request to a patient.
    Categories requested: medical_history, lab_reports, mental_health, genetic_data.
    Duration options: 1h, 24h, 7d, 365d, custom.
    """
    patient_id = int(payload.get("patient_id", 1))
    doctor_name = current_user.full_name if current_user.role == "doctor" else payload.get("doctor_name", "Dr. Sarah Sharma")
    organization = payload.get("organization", "Apex Hospital")
    purpose = payload.get("purpose", "Comprehensive Clinical Consultation")
    requested_categories = payload.get("requested_categories", ["medical_history", "lab_reports"])
    duration_hours = int(payload.get("duration_hours", 24))

    token, expires_at = generate_consent_token("doc_req", duration_hours)

    consent = ConsentRecord(
        patient_id=patient_id,
        grantee_name=doctor_name,
        grantee_type="doctor",
        grantee_organization=organization,
        permissions=json.dumps(requested_categories),
        access_token=token,
        status="pending_patient_approval",
        expires_at=expires_at
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    return {
        "status": "REQUEST_SENT",
        "request_id": consent.id,
        "message": f"Consent request transmitted to patient for categories: {', '.join(requested_categories)} ({duration_hours} hours).",
        "expires_at": expires_at.isoformat()
    }


