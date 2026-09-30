import urllib.request
import json

def post(url, data, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, data=json.dumps(data).encode(), headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

# 1. Login
login_res = post('http://127.0.0.1:8000/api/auth/login', {'email': 'patient@example.com', 'password': 'patient123'})
token = login_res['access_token']
print("Login successful! Patient:", login_res['user']['full_name'])
print("Patient Allergies:", login_res['user']['drug_allergies'])

# 2. Test Adaptive Questions
q_res = post('http://127.0.0.1:8000/api/navigator/questions', {'symptoms': ['high_fever', 'dry_cough']}, token)
print(f"\nAdaptive Questions generated: {len(q_res['questions'])}")
for q in q_res['questions']:
    print(" •", q['question'])

# 3. Test Navigator Assessment with Triage & XAI
assess_res = post('http://127.0.0.1:8000/api/navigator/assess', {
    'symptoms': ['high_fever', 'productive_cough_phlegm', 'breathlessness_shortness_of_breath'],
    'qa_answers': {'duration_days': '3-5 days', 'severity_scale': '7 - 8'},
    'uploaded_report_ids': []
}, token)
print("\nMultimodal Assessment Result:")
print(" Disease:", assess_res['top_disease'], f"({assess_res['confidence_percentage']}%)")
print(" Triage Level:", assess_res['triage']['triage_level'])
print(" Action:", assess_res['triage']['action_text'])
print(" Explainable AI (XAI):", assess_res['xai_reasoning'])

# 4. Test Medication Safety Checker (Allergy Detection)
safety_res = post('http://127.0.0.1:8000/api/prescriptions/safety-check', {
    'consultation_id': 1,
    'medicines': [{'name': 'Amoxicillin 500mg', 'dosage': '500mg', 'timing': '1-0-1', 'duration': '5 days'}]
}, token)
print("\nMedication Safety Check Test (Prescribing Amoxicillin to Penicillin-allergic patient):")
print(" Is Safe:", safety_res['is_safe'])
print(" Alerts Detected:", safety_res['alert_count'])
for a in safety_res['alerts']:
    print(f" [{a['type']}] {a['message']}")
