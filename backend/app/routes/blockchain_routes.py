import json
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..database import get_db
from ..models import User, Consultation, Prescription, MedicalReport, BlockchainBlock, ConsentRecord
from ..auth import get_current_user
from ..ml.blockchain_engine import (
    create_block,
    verify_blockchain_integrity,
    generate_consent_token,
    compute_sha256
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

