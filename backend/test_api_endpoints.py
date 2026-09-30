import sys
from fastapi.testclient import TestClient
from backend.app.main import app

def main():
    client = TestClient(app)

    # 0. Authenticate as demo patient (Rahul)
    login_res = client.post('/api/auth/login', json={
        "email": "patient@example.com",
        "password": "patient123"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("[OK] 0. Authenticated successfully as Rahul Verma (Patient ID 4).")

    # 1. Symptoms Catalog
    res = client.get('/api/closed-loop/symptoms-catalog')
    assert res.status_code == 200, f"Catalog failed: {res.status_code}"
    cat = res.json()
    print(f"[OK] 1. Symptoms Catalog: {cat['total_symptoms_count']} symptoms across {len(cat['categories'])} categories.")

    # 2. Uncertainty Assessment
    res = client.post('/api/closed-loop/uncertainty-assess', json={
        "symptoms": ["chest_pain_pressure", "shortness_of_breath"]
    }, headers=headers)
    assert res.status_code == 200, f"Uncertainty failed: {res.status_code}"
    u = res.json()
    print(f"[OK] 2. Uncertainty Assessment: H(D)={u['shannon_entropy']} bits, Uncertainty={u['uncertainty_score']}%, Condition='{u['top_candidate']['disease']}'.")

    # 3. Next Best Question
    res = client.post('/api/closed-loop/next-question', json={
        "symptoms": ["chest_pain_pressure", "shortness_of_breath"],
        "answered_question_ids": []
    }, headers=headers)
    assert res.status_code == 200, f"Next question failed: {res.status_code}"
    q = res.json()
    print(f"[OK] 3. Next Best Question: Has question: {q['has_next_question']}, Data: {q.get('next_question')}")

    # 4. Minimum Diagnostic Test Set Optimization
    res = client.post('/api/closed-loop/minimum-tests', json={
        "top_disease": "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
        "current_uncertainty": 55.0,
        "symptoms": ["chest_pain_pressure", "shortness_of_breath"],
        "triage_level": "Emergency Care"
    }, headers=headers)
    assert res.status_code == 200, f"Optimize tests failed: {res.status_code}"
    t = res.json()
    print(f"[OK] 4. Minimum Test Optimizer: Recommended {len(t['minimum_test_set'])} tests, Total Cost: Rs.{t['total_estimated_cost_inr']}, Residual Uncertainty: {t['expected_residual_uncertainty_pct']}%.")

    # 5. Explainable Decision Map
    res = client.post('/api/closed-loop/explainable-decision-map', json={
        "target_disease": "Acute Coronary Syndrome / Angina (Cardiac Emergency)",
        "symptoms": ["chest_pain_pressure", "shortness_of_breath"]
    }, headers=headers)
    assert res.status_code == 200, f"Decision map failed: {res.status_code}"
    edm = res.json()
    print(f"[OK] 5. Explainable Decision Map: {len(edm['positive_attributions'])} positive factors (+{edm['net_positive_score']}), {len(edm['missing_information_penalties'])} missing parameters.")

    # 6. Context-Aware Passport Generation & Public View
    res = client.post('/api/closed-loop/passport/generate-token', json={
        "context_scope": "PUBLIC_BASIC"
    }, headers=headers)
    assert res.status_code == 200, f"Passport gen failed: {res.status_code}"
    pgen = res.json()
    print(f"[OK] 6. Contextual Token Generated: '{pgen['token']}', Scope: '{pgen['scope_label']}'.")

    # 7. View Contextual Passport
    res = client.get(pgen['qr_access_url'])
    assert res.status_code == 200, f"Passport view failed: {res.status_code}"
    pview = res.json()
    print(f"[OK] 7. Dynamic Passport View: Blood Group={pview.get('blood_group')}, Name={pview.get('full_name')}, Scope={pview.get('scope_label')}.")

    # 8. Longitudinal Digital Health Timeline
    res = client.get('/api/closed-loop/timeline/patient/4', headers=headers)
    assert res.status_code == 200, f"Timeline failed: {res.status_code}"
    tline = res.json()
    print(f"[OK] 8. Longitudinal Timeline: Retrieved {len(tline['timeline_entries'])} milestones.")

    # 9. AI Calibration & Disagreement Telemetry
    res = client.get('/api/closed-loop/ai-performance-calibration', headers=headers)
    assert res.status_code == 200, f"Calibration failed: {res.status_code}"
    cal = res.json()
    print(f"[OK] 9. Calibration Telemetry: Cases={cal['total_cases_analyzed']}, AI Accuracy={cal['ai_accuracy_percentage']}%, Doctor Accuracy={cal['doctor_accuracy_percentage']}%, Override Precision={cal['clinician_override_precision']}%.")

    print("\n=======================================================")
    print("ALL 9 CLOSED-LOOP FASTAPI ENDPOINTS PASSED WITH 100% SUCCESS!")
    print("=======================================================")

if __name__ == '__main__':
    main()
