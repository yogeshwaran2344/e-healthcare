"""
Verification test script for all 6 Advanced Add-Ons.
Tests:
1. AI + Predictive Care & Chronic Alerts
2. IoT Wearables & Live Telemetry Stream
3. Blockchain Health Records & Proof of Integrity
4. Smart Hospital Navigation & Priority Queue
5. Rapid SOS Emergency Dispatch & Live Ambulance
6. Community & Preventive Health Moderation
"""

from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def run_tests():
    print("--- 1. Testing Login as Patient ---")
    login_resp = client.post("/api/auth/login", json={"email": "patient@example.com", "password": "patient123"})
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login OK. Patient Token acquired.")

    print("\n--- 2. Testing AI + Predictive Care & Chronic Alerts ---")
    pred_resp = client.get("/api/predictive/assessment", headers=headers)
    assert pred_resp.status_code == 200, f"Predictive failed: {pred_resp.text}"
    pred_data = pred_resp.json()
    print(f"Risk Score: {pred_data['assessment']['risk_score']} | Urgency: {pred_data['assessment']['urgency_level']}")
    print(f"Suggested Timeline: {pred_data['assessment']['suggested_timeline']} | Specialist: {pred_data['assessment']['recommended_specialist']}")

    chronic_resp = client.get("/api/predictive/chronic-alerts", headers=headers)
    assert chronic_resp.status_code == 200
    print(f"Active Chronic Alerts: {len(chronic_resp.json()['alerts'])}")

    print("\n--- 3. Testing IoT Wearables & Vitals Stream ---")
    devices_resp = client.get("/api/iot/devices", headers=headers)
    assert devices_resp.status_code == 200
    devices = devices_resp.json()
    print(f"Connected Devices: {len(devices)} (e.g. {devices[0]['device_name']})")

    vitals_resp = client.get("/api/iot/vitals/latest", headers=headers)
    assert vitals_resp.status_code == 200
    vitals = vitals_resp.json()["telemetry_stream"]
    for k, v in vitals.items():
        print(f"  IoT Metric [{k}]: {v['primary_value']} {v['unit']} ({v['alert_severity']})")

    # Simulate emergency anomaly
    sim_resp = client.post("/api/iot/simulate-stream?device_type=spo2&trigger_emergency=true", headers=headers)
    assert sim_resp.status_code == 200
    print(f"Simulated Anomaly: {sim_resp.json()['alert_message']} (Severity: {sim_resp.json()['alert_severity']})")

    print("\n--- 4. Testing Blockchain Health Records & Proof of Integrity ---")
    ledger_resp = client.get("/api/blockchain/ledger", headers=headers)
    assert ledger_resp.status_code == 200
    blocks = ledger_resp.json()["chain"]
    print(f"Total Blockchain Blocks: {len(blocks)}")
    print(f"Genesis Hash: {blocks[0]['block_hash'][:16]}... | Prev Hash: {blocks[0]['previous_hash'][:16]}...")

    verify_resp = client.post("/api/blockchain/verify-integrity", headers=headers)
    assert verify_resp.status_code == 200
    print(f"Integrity Status: {verify_resp.json()['verification_status']}")
    assert verify_resp.json()["is_valid"] is True

    consents_resp = client.get("/api/blockchain/consents", headers=headers)
    assert consents_resp.status_code == 200
    print(f"Active Consent Records: {len(consents_resp.json())}")

    # Demonstrable Document Verification Test
    print("Testing End-to-End Report Upload & File SHA-256 Ledger Anchor...")
    sample_file_bytes = b"Hemoglobin: 13.2 g/dL, WBC: 7400/mcL, Platelets: 240,000/mcL"
    up_res = client.post(
        "/api/reports/upload",
        headers=headers,
        data={"report_type": "Complete Blood Count"},
        files={"file": ("cbc_automated_test.txt", sample_file_bytes, "text/plain")}
    )
    assert up_res.status_code == 200
    report_data = up_res.json()
    print(f"Report Anchored: ID #{report_data['id']} | SHA-256: {report_data['file_sha256'][:16]}... | Block: {report_data['blockchain_block_hash'][:16]}...")

    # Authentic check
    v_auth = client.post(
        "/api/blockchain/verify-document-file",
        headers=headers,
        data={"record_id": str(report_data["id"]), "record_type": "LAB_REPORT"},
        files={"file": ("cbc_automated_test.txt", sample_file_bytes, "text/plain")}
    )
    assert v_auth.status_code == 200
    assert v_auth.json()["is_authentic"] is True
    assert v_auth.json()["status"] == "MATCH"
    print(f"Authentic File Verification: {v_auth.json()['status']} ({v_auth.json()['verdict']})")

    # Tampered check
    tampered_bytes = b"Hemoglobin: 19.9 g/dL [MODIFIED_FOR_TAMPER_TEST]"
    v_tamper = client.post(
        "/api/blockchain/verify-document-file",
        headers=headers,
        data={"record_id": str(report_data["id"]), "record_type": "LAB_REPORT"},
        files={"file": ("cbc_automated_test.txt", tampered_bytes, "text/plain")}
    )
    assert v_tamper.status_code == 200
    assert v_tamper.json()["is_authentic"] is False
    assert v_tamper.json()["status"] == "MISMATCH"
    print(f"Tampered File Verification: {v_tamper.json()['status']} ({v_tamper.json()['verdict']})")

    print("\n--- 5. Testing Indoor Hospital Navigation & Queue ---")
    floors_resp = client.get("/api/navigation/floors")
    assert floors_resp.status_code == 200
    print(f"Hospital Floors Loaded: {list(floors_resp.json()['floors'].keys())}")

    route_resp = client.get("/api/navigation/route?start=ENTRANCE&destination=OPD_PULMONOLOGY")
    assert route_resp.status_code == 200
    route = route_resp.json()
    print(f"Route: {route['start']} -> {route['destination']} ({route['total_distance_meters']}m, {route['estimated_walk_minutes']} mins)")
    print(f"Steps: {len(route['directions'])} directions, {len(route['ar_camera_hud'])} AR HUD waypoints")

    queue_resp = client.get("/api/queue/my-token", headers=headers)
    assert queue_resp.status_code == 200
    q = queue_resp.json()
    print(f"My Queue Token: {q['token_code']} | Serving: {q['currently_serving_token']} | Est Wait: {q['estimated_wait_minutes']} mins")

    print("\n--- 6. Testing Rapid SOS Emergency Dispatch & Ambulance Tracking ---")
    sos_resp = client.post("/api/emergency/trigger-sos", json={"emergency_type": "SOS_MANUAL", "latitude": 12.9716, "longitude": 77.5946}, headers=headers)
    assert sos_resp.status_code == 200
    sos_data = sos_resp.json()
    print(f"SOS Dispatched: {sos_data['ambulance_unit']} | ETA: {sos_data['eta_minutes']} mins | Bay: {sos_data['assigned_trauma_bay']}")

    status_resp = client.get(f"/api/emergency/active-status?alert_id={sos_data['alert_id']}", headers=headers)
    assert status_resp.status_code == 200
    print(f"Ambulance Live Tracking: {status_resp.json()['telemetry']['status_text']}")

    print("\n--- 7. Testing Community Health & Preventive Gamification ---")
    groups_resp = client.get("/api/community/groups")
    assert groups_resp.status_code == 200
    print(f"Community Groups: {len(groups_resp.json())}")

    posts_resp = client.get("/api/community/posts")
    assert posts_resp.status_code == 200
    posts = posts_resp.json()
    print(f"Community Posts: {len(posts)} (AI Verified Safe: {posts[0]['is_ai_verified']})")

    challenges_resp = client.get("/api/preventive/challenges", headers=headers)
    assert challenges_resp.status_code == 200
    challenges = challenges_resp.json()
    print(f"Active Wellness Challenges: {len(challenges)} (e.g. {challenges[0]['title']}: {challenges[0]['progress_percent']}%)")

    rewards_resp = client.get("/api/preventive/rewards", headers=headers)
    assert rewards_resp.status_code == 200
    rewards = rewards_resp.json()
    print(f"Patient Reward Points: {rewards['total_points']} ({rewards['tier_level']}) | Badges: {len(rewards['badges'])}")

    coach_resp = client.get("/api/preventive/lifestyle-coach", headers=headers)
    assert coach_resp.status_code == 200
    print(f"AI Lifestyle Coach: {coach_resp.json()['nutrition_plan']['dietary_framework']}")

    print("\n==========================================")
    print("ALL 6 ADVANCED ADD-ONS VERIFIED 100% OK!")
    print("==========================================")

if __name__ == "__main__":
    run_tests()
