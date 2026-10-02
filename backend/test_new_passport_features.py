import sys
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_new_features():
    print("Testing New Health Passport & Access Features...")
    
    # 1. Login as patient
    login_res = client.post("/api/auth/login", json={"email": "patient@example.com", "password": "patient123"})
    assert login_res.status_code == 200, f"Patient login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[PASS] 1. Patient Login Successful")

    # 2. Test Access History
    acc_res = client.get("/api/blockchain/access-history", headers=headers)
    assert acc_res.status_code == 200, f"Access history failed: {acc_res.text}"
    history = acc_res.json().get("access_history", [])
    assert len(history) > 0, "Access history should have records"
    print(f"[PASS] 2. Access History retrieved ({len(history)} records found)")

    # 3. Test Break-Glass Emergency Access
    bg_payload = {
        "patient_id": 4,
        "hospital": "Apex Super-Specialty ER Trauma Bay 1",
        "justification": "Severe acute respiratory distress with hemodynamic instability; immediate access required."
    }
    bg_res = client.post("/api/blockchain/break-glass", json=bg_payload, headers=headers)
    assert bg_res.status_code == 200, f"Break glass failed: {bg_res.text}"
    bg_data = bg_res.json()
    assert "EMERGENCY_BREAK_GLASS_ACTIVE" in bg_data["status"]
    assert "emergency_data" in bg_data
    print(f"[PASS] 3. Emergency Break-Glass Override executed at Block #{bg_data['block_index']}")

    # 4. Test Break-Glass Logs
    bg_logs_res = client.get("/api/blockchain/break-glass-logs", headers=headers)
    assert bg_logs_res.status_code == 200
    logs = bg_logs_res.json().get("break_glass_records", [])
    assert len(logs) > 0
    print(f"[PASS] 4. Break-Glass audit logs retrieved ({len(logs)} records)")

    # 5. Test Digital Health Passport for Travel
    travel_payload = {
        "destination_country": "United Kingdom",
        "travel_date": "2026-10-20",
        "purpose": "Academic Conference",
        "include_vaccines": True,
        "include_allergies": True,
        "include_fit_to_fly": True
    }
    travel_res = client.post("/api/blockchain/travel-passport", json=travel_payload, headers=headers)
    assert travel_res.status_code == 200, f"Travel passport failed: {travel_res.text}"
    t_data = travel_res.json()
    assert "TRAVEL-" in t_data["travel_token"]
    print(f"[PASS] 5. Travel Health Passport generated: Token {t_data['travel_token']} (Destination: {t_data['destination']})")

    # 6. Test Doctor License Verification
    doc_res = client.get("/api/doctors/verify-license/2")
    assert doc_res.status_code == 200, f"Doctor license check failed: {doc_res.text}"
    doc_data = doc_res.json()
    assert doc_data["verified"] is True
    print(f"[PASS] 6. Doctor License Verified: {doc_data['license_number']} ({doc_data['status']})")

    # 7. Test Hospital Portal Route
    hosp_res = client.get("/hospital")
    assert hosp_res.status_code == 200
    print("[PASS] 7. Hospital Portal endpoint (/hospital) serving HTML successfully")

    print("\nALL NEW HEALTH PASSPORT SUITE FEATURES VALIDATED 100%!")

if __name__ == "__main__":
    test_new_features()
