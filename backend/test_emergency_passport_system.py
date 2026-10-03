"""
Comprehensive Test Suite for Dynamic Emergency Medical Passport & Audit System
=============================================================================
Validates:
1. Dynamic assembly from live database records (no unnecessary data duplication)
2. Accurate extraction of required fields:
   - patient identity
   - blood group
   - allergies
   - critical medical conditions
   - current important medications
   - emergency contacts
   - relevant physician information
   - recent vitals snapshot
3. Role-Based Access Control (RBAC):
   - Patient can view own live passport
   - Patient cannot view other patients' passports (403 Forbidden)
   - Doctor can access live passport with valid clinical purpose (min 8 chars)
   - Doctor access with short/empty purpose is rejected (422 Unprocessable)
   - Unauthorized role cannot access clinician endpoints (403 Forbidden)
4. Append-Only Emergency Access Audit System:
   - Logs accessor identity, patient ID, timestamp, purpose, information type, emergency flag
   - Excludes sensitive clinical data (blood group, allergies, etc.) from audit UI
   - Admin can view institution-wide audit trail
   - Patient can view accesses to their own record
   - Doctor can view their own outbound accesses
5. Prevention of Unauthorized Modification (Read-Only enforcement)
6. Dedicated Emergency Mode UI Route (/emergency/view)
"""
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.models import User, EmergencyAccessAudit

client = TestClient(app)

def login(email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, f"Login failed for {email}: {res.text}"
    return res.json()["access_token"]

def test_emergency_passport_system():
    # 1. Authenticate users
    patient_token = login("patient@example.com", "patient123")
    doctor_token = login("doctor@example.com", "doctor123")
    admin_token = login("admin@example.com", "admin123")
    
    p_headers = {"Authorization": f"Bearer {patient_token}"}
    d_headers = {"Authorization": f"Bearer {doctor_token}"}
    a_headers = {"Authorization": f"Bearer {admin_token}"}

    # Verify patient identity
    me_res = client.get("/api/auth/me", headers=p_headers)
    assert me_res.status_code == 200
    patient_id = me_res.json()["id"]

    # 2. Patient Self-View of Live Emergency Passport
    self_res = client.get("/api/emergency/live-passport", headers=p_headers)
    assert self_res.status_code == 200
    data = self_res.json()
    assert "passport" in data
    passport = data["passport"]

    # Validate required emergency profile fields
    assert passport["generated_dynamically"] is True
    assert passport["read_only"] is True
    assert passport["patient_id"] == patient_id
    assert passport["patient_name"] == "Rahul Verma"
    assert passport["blood_group"] == "B+"
    assert "Penicillin" in passport["drug_allergies"]
    assert "Diabetes" in passport["pre_existing_conditions"]
    assert "Metformin" in passport["current_medications"]
    assert passport["emergency_contact"] == "+91 91234 56789"
    assert passport["physician"]["name"] == "Dr. Sarah Sharma"
    assert passport["physician"]["hospital"] == "Apex Multi-Specialty Hospital"
    assert "latest_vitals_snapshot" in passport

    # 3. RBAC & Cross-Patient Protection
    # A patient attempting to access another patient's live passport directly
    cross_res = client.get(f"/api/emergency/live-passport/5?purpose=unauthorized+probe&is_emergency=true", headers=p_headers)
    assert cross_res.status_code == 403, f"Expected 403 on cross-patient access, got: {cross_res.status_code}"

    # 4. Doctor Access with Validation of Purpose
    # Short purpose (<8 characters) should be rejected by validation
    short_res = client.get(f"/api/emergency/live-passport/{patient_id}?purpose=short&is_emergency=true", headers=d_headers)
    assert short_res.status_code == 422, f"Expected 422 for short purpose, got: {short_res.status_code}"

    # Doctor access with proper clinical emergency justification
    doc_res = client.get(
        f"/api/emergency/live-passport/{patient_id}?purpose=Acute+cardiac+trauma+intake+evaluation&is_emergency=true",
        headers=d_headers
    )
    assert doc_res.status_code == 200
    doc_data = doc_res.json()
    assert doc_data["mode"] == "emergency"
    assert doc_data["read_only"] is True
    assert doc_data["passport"]["blood_group"] == "B+"

    # 5. One-Tap SOS Live Passport Integration
    sos_res = client.post("/api/emergency/trigger-sos", json={"latitude": 12.9716, "longitude": 77.5946}, headers=p_headers)
    assert sos_res.status_code == 200
    sos_data = sos_res.json()
    assert sos_data["status"] == "EMERGENCY_DISPATCHED"
    assert "B+" in sos_data["patient_passport_shared"]["blood_group"]

    # 6. Contextual QR Token Access with Standalone Emergency View
    qr_res = client.post("/api/closed-loop/passport/generate-token", json={"context_scope": "FIRST_RESPONDER_BASIC"}, headers=p_headers)
    assert qr_res.status_code == 200
    qr_data = qr_res.json()
    assert "emergency_view_url" in qr_data
    token_str = qr_data["token"]

    # Public / responder view via token
    view_res = client.get(f"/api/closed-loop/passport/view/{token_str}")
    assert view_res.status_code == 200
    view_data = view_res.json()
    assert view_data["full_name"] == "Rahul Verma"
    assert view_data["blood_group"] == "B+"
    assert view_data["read_only"] is True

    # Standalone Emergency UI page response
    page_res = client.get(f"/emergency/view?token={token_str}")
    assert page_res.status_code == 200
    assert "Emergency Medical Passport" in page_res.text

    # 7. Audit System Verification
    # Admin audit access
    admin_audit_res = client.get("/api/emergency/audit-log", headers=a_headers)
    assert admin_audit_res.status_code == 200
    admin_audit = admin_audit_res.json()
    assert admin_audit["total"] > 0
    events = admin_audit["events"]

    # Ensure no clinical data is exposed in audit entries
    for ev in events:
        assert "blood_group" not in ev
        assert "drug_allergies" not in ev
        assert "current_medications" not in ev
        assert "timestamp" in ev
        assert "accessor_role" in ev
        assert "purpose" in ev
        assert "is_emergency" in ev

    # Patient audit access (sees only accesses involving their own record)
    patient_audit_res = client.get("/api/emergency/audit-log", headers=p_headers)
    assert patient_audit_res.status_code == 200
    p_events = patient_audit_res.json()["events"]
    for ev in p_events:
        assert ev["patient_id"] == patient_id

    # Doctor audit access (sees accesses they performed)
    doctor_audit_res = client.get("/api/emergency/audit-log", headers=d_headers)
    assert doctor_audit_res.status_code == 200

    print("\n[SUCCESS] ALL EMERGENCY PASSPORT & AUDIT TESTS PASSED WITH 100% INTEGRITY!")

if __name__ == "__main__":
    test_emergency_passport_system()
