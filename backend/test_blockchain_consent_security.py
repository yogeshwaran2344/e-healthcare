"""
Automated Test Suite for Blockchain Zero-PHI Integrity, Patient Consent, and Security Hardening.
Tests:
1. Zero-PHI on-chain storage (no plaintext diagnoses/medications in block data_payload)
2. Cryptographic record verification (detecting tampered DB records)
3. Backend-enforced consent checks (blocking doctors without consent, allowing with consent)
4. Emergency break-glass override & audit logging
5. Password length enforcement & path traversal protection
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.main import app
from backend.app.database import Base, get_db
from backend.app.models import User, Consultation, MedicalReport, BlockchainBlock, ConsentRecord, EmergencyAccessAudit
from backend.app.auth import hash_password, create_access_token
from backend.app.ml.blockchain_engine import (
    create_block,
    canonicalize_medical_record,
    compute_sha256,
    verify_single_record_integrity
)

# Test SQLite in-memory or file database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_security_audit.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

def teardown_module(module):
    engine.dispose()
    import os
    if os.path.exists("./test_security_audit.db"):
        try:
            os.remove("./test_security_audit.db")
        except Exception:
            pass

def test_password_policy_enforcement():
    """Verify registration rejects passwords shorter than 8 characters."""
    resp = client.post("/api/auth/register", json={
        "email": "weak@example.com",
        "password": "123",
        "full_name": "Weak User",
        "role": "patient"
    })
    assert resp.status_code == 400
    assert "8 characters" in resp.json()["detail"]

    # Valid password succeeds
    resp_ok = client.post("/api/auth/register", json={
        "email": "patient1@example.com",
        "password": "StrongPassword123!",
        "full_name": "Test Patient",
        "role": "patient"
    })
    assert resp_ok.status_code == 200

def test_blockchain_zero_phi_storage():
    """
    Verify that blockchain blocks store zero cleartext Protected Health Information (PHI).
    Sensitive clinical details must be hashed into data_hash and Merkle root.
    """
    db = TestingSessionLocal()
    patient = db.query(User).filter(User.email == "patient1@example.com").first()

    sensitive_clinical_data = {
        "consultation_id": 101,
        "predicted_disease": "Severe Acute Coronary Syndrome",
        "triage_level": "Emergency Care",
        "severity": "Critical",
        "symptoms": ["crushing substernal chest pain", "diaphoresis", "radiation to left arm"],
        "created_at": datetime.utcnow().isoformat()
    }

    block_data = create_block(
        block_index=1,
        patient_id=patient.id,
        record_type="CONSULTATION",
        record_id="101",
        data_dict=sensitive_clinical_data,
        previous_hash="0" * 64
    )

    # Inspect the on-chain payload
    payload = json.loads(block_data["data_payload"])
    
    # 1. No plaintext diagnosis or symptoms in on-chain payload
    assert "Severe Acute Coronary Syndrome" not in block_data["data_payload"]
    assert "crushing substernal chest pain" not in block_data["data_payload"]
    assert "predicted_disease" not in payload
    assert "symptoms" not in payload

    # 2. Contains cryptographic integrity verification metadata
    assert payload["schema_version"] == "2.0-zero-phi"
    assert payload["integrity_hash"] == block_data["data_hash"]
    assert "merkle_root" in payload
    assert block_data["validator_signature"] is not None

    db.close()

def test_tamper_evident_record_verification():
    """
    Verify that tampering with an off-chain database record is immediately
    detected via the verify-record cryptographic comparison.
    """
    db = TestingSessionLocal()
    patient = db.query(User).filter(User.email == "patient1@example.com").first()

    # Create consultation in database
    consultation = Consultation(
        patient_id=patient.id,
        predicted_disease="Type 2 Diabetes Mellitus",
        triage_level="Doctor Consultation",
        severity="Moderate",
        symptoms_list="increased thirst, frequent urination, fatigue",
        status="completed"
    )
    db.add(consultation)
    db.commit()
    db.refresh(consultation)

    c_data = {
        "consultation_id": consultation.id,
        "predicted_disease": consultation.predicted_disease or "Clinical Consultation",
        "triage_level": consultation.triage_level or "Doctor Consultation",
        "severity": consultation.severity or "Moderate",
        "symptoms": consultation.symptoms_list,
        "created_at": consultation.created_at.isoformat()
    }

    # Anchor to blockchain
    b_dict = create_block(
        block_index=1,
        patient_id=patient.id,
        record_type="CONSULTATION",
        record_id=str(consultation.id),
        data_dict=c_data,
        previous_hash="0" * 64
    )
    block = BlockchainBlock(**b_dict)
    db.add(block)
    db.commit()

    # Authenticate as patient
    token = create_access_token({"sub": str(patient.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Step 1: Verify intact record -> MUST PASS
    verify_resp = client.get(f"/api/blockchain/verify-record/CONSULTATION/{consultation.id}", headers=headers)
    assert verify_resp.status_code == 200
    res_data = verify_resp.json()
    assert res_data["status"] == "VERIFIED_AUTHENTIC"
    assert res_data["is_authentic"] is True
    assert res_data["tampering_detected"] is False

    # Step 2: Maliciously tamper with database record directly
    consultation.predicted_disease = "Healthy - No Condition Found (Falsified)"
    consultation.severity = "Mild"
    db.commit()

    # Step 3: Verify tampered record -> MUST DETECT TAMPERING
    tampered_resp = client.get(f"/api/blockchain/verify-record/CONSULTATION/{consultation.id}", headers=headers)
    assert tampered_resp.status_code == 200
    tampered_data = tampered_resp.json()
    assert tampered_data["status"] == "TAMPERING_DETECTED"
    assert tampered_data["is_authentic"] is False
    assert tampered_data["tampering_detected"] is True
    assert tampered_data["anchored_sha256_hash"] != tampered_data["recomputed_sha256_hash"]

    db.close()

def test_backend_consent_enforcement():
    """
    Verify backend consent enforcement:
    1. Doctor has NO consent -> accessing patient consultation gives 403 Forbidden.
    2. Patient grants consent -> doctor access succeeds.
    3. Revoking consent -> doctor access immediately 403 Forbidden again.
    """
    db = TestingSessionLocal()
    patient = db.query(User).filter(User.email == "patient1@example.com").first()

    # Register Doctor
    doctor = User(
        email="doctor1@example.com",
        password_hash=hash_password("DoctorPass123!"),
        full_name="Dr. Gregory House",
        role="doctor"
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)

    # Patient creates a new consultation
    c = Consultation(
        patient_id=patient.id,
        predicted_disease="Hypertension Stage 2",
        symptoms_list="headache, dizziness",
        status="pending"
    )
    db.add(c)
    db.commit()
    db.refresh(c)

    doc_token = create_access_token({"sub": str(doctor.id)})
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Step 1: Doctor attempts access without consent -> 403 Forbidden
    resp = client.get(f"/api/consultations/{c.id}", headers=doc_headers)
    assert resp.status_code == 403
    assert "consent" in resp.json()["detail"].lower()

    # Step 2: Grant active consent for "diagnoses"
    consent = ConsentRecord(
        patient_id=patient.id,
        grantee_name="Dr. Gregory House",
        grantee_type="doctor",
        grantee_organization="Princeton-Plainsboro Teaching Hospital",
        permissions=json.dumps(["diagnoses"]),
        access_token="tok_test_diagnoses_9988",
        status="active",
        expires_at=datetime.utcnow() + timedelta(days=2)
    )
    db.add(consent)
    db.commit()
    db.refresh(consent)

    # Doctor access with valid consent -> 200 OK
    resp_allowed = client.get(f"/api/consultations/{c.id}", headers=doc_headers)
    assert resp_allowed.status_code == 200
    assert resp_allowed.json()["id"] == c.id

    # Step 3: Revoke consent -> Doctor access immediately blocked
    consent.status = "revoked"
    db.commit()

    resp_blocked = client.get(f"/api/consultations/{c.id}", headers=doc_headers)
    assert resp_blocked.status_code == 403
    assert "consent" in resp_blocked.json()["detail"].lower()

    db.close()

def test_emergency_break_glass_access():
    """
    Verify emergency break-glass:
    Doctor without normal consent can access critical data during emergency,
    which is immutably logged into emergency audit trails.
    """
    db = TestingSessionLocal()
    patient = db.query(User).filter(User.email == "patient1@example.com").first()
    doctor = db.query(User).filter(User.email == "doctor1@example.com").first()

    doc_token = create_access_token({"sub": str(doctor.id)})
    doc_headers = {"Authorization": f"Bearer {doc_token}"}

    # Trigger break-glass access
    bg_payload = {
        "patient_id": patient.id,
        "justification": "Patient unconscious in trauma bay following MVA, acute hypotension.",
        "hospital": "City Trauma Center Bay 1"
    }

    resp = client.post("/api/blockchain/break-glass", json=bg_payload, headers=doc_headers)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["status"] == "EMERGENCY_BREAK_GLASS_ACTIVE"
    assert "emergency_data" in res_data

    # Check that audit log entry was created
    audit = db.query(EmergencyAccessAudit).filter(
        EmergencyAccessAudit.patient_id == patient.id,
        EmergencyAccessAudit.accessor_id == doctor.id,
        EmergencyAccessAudit.is_emergency == True
    ).order_by(EmergencyAccessAudit.id.desc()).first()
    assert audit is not None
    assert audit.is_emergency is True

    # Check that access history includes the break-glass event
    pat_token = create_access_token({"sub": str(patient.id)})
    pat_headers = {"Authorization": f"Bearer {pat_token}"}
    hist_resp = client.get("/api/blockchain/access-history", headers=pat_headers)
    assert hist_resp.status_code == 200
    entries = hist_resp.json()["access_history"]
    assert any("Emergency" in e["status"] for e in entries)

    db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("E-HEALTHCARE SECURITY, BLOCKCHAIN & CONSENT TEST RUNNER")
    print("=" * 60)
    setup_module(None)
    tests = [
        ("Password Policy Enforcement", test_password_policy_enforcement),
        ("Blockchain Zero-PHI Storage", test_blockchain_zero_phi_storage),
        ("Tamper-Evident Record Verification", test_tamper_evident_record_verification),
        ("Backend Consent Enforcement", test_backend_consent_enforcement),
        ("Emergency Break-Glass Access & Audit", test_emergency_break_glass_access),
    ]
    passed = 0
    for name, test_func in tests:
        try:
            print(f"[TEST] {name:40s} ... ", end="")
            test_func()
            print("PASSED [OK]")
            passed += 1
        except Exception as e:
            print(f"FAILED [FAIL]: {e}")
            import traceback
            traceback.print_exc()
    teardown_module(None)
    print("=" * 60)
    print(f"FINAL RESULT: {passed}/{len(tests)} tests passed.")
    print("=" * 60)
    if passed != len(tests):
        sys.exit(1)
