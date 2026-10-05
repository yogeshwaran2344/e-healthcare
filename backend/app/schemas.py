from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth & User Profile Schemas
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "patient"  # "patient" or "doctor"
    phone: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    pre_existing_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    drug_allergies: Optional[str] = None
    # If doctor:
    specialization: Optional[str] = None
    qualification: Optional[str] = None
    license_number: Optional[str] = None
    experience_years: Optional[int] = 5

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    pre_existing_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    drug_allergies: Optional[str] = None

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    role: str
    phone: Optional[str] = None
    age: Optional[int] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    pre_existing_conditions: Optional[str] = None
    current_medications: Optional[str] = None
    drug_allergies: Optional[str] = None
    specialization: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

# Doctor Schemas
class DoctorOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    email: str
    specialization: str
    qualification: str
    license_number: str
    experience_years: int
    hospital_affiliation: str
    bio: Optional[str] = None
    is_available: bool

# Health Navigator & Adaptive QA Schemas
class AdaptiveQuestionsRequest(BaseModel):
    symptoms: List[str]

class QuestionItem(BaseModel):
    id: str
    question: str
    type: str
    options: List[str]

class AdaptiveQuestionsResponse(BaseModel):
    questions: List[QuestionItem]

# Legacy / Basic Predict Schemas for backwards compatibility
class PredictRequest(BaseModel):
    symptoms: List[str]

class DiseasePossibility(BaseModel):
    disease: str
    confidence_percentage: float
    specialist: str

class PredictResponse(BaseModel):
    top_disease: str
    confidence_percentage: float
    severity: str
    specialist_recommended: str
    specialist_domain: Optional[str] = "Clinical Medicine"
    specialist_rationale: Optional[str] = None
    medical_advice: str
    recommended_diagnostic_tests: List[str]
    needs_lab_reports: bool
    report_instructions: str
    other_possibilities: List[DiseasePossibility]

class NavigatorAssessmentRequest(BaseModel):
    symptoms: List[str]
    qa_answers: Dict[str, Any] = {}
    uploaded_report_ids: Optional[List[int]] = []

class TriageResult(BaseModel):
    triage_level: str  # "Self-Care", "Doctor Consultation", "Emergency Care"
    badge_color: str
    action_text: str
    triage_reasons: List[str]

class NavigatorAssessmentResponse(BaseModel):
    top_disease: str
    confidence_percentage: float
    severity: str
    specialist_recommended: str
    specialist_domain: Optional[str] = "Clinical Medicine"
    specialist_rationale: Optional[str] = None
    medical_advice: str
    recommended_diagnostic_tests: List[str]
    triage: TriageResult
    xai_reasoning: List[str]
    biomarkers_detected: Dict[str, Any] = {}
    other_possibilities: List[Dict[str, Any]] = []
    # Closed-loop additions
    entropy_uncertainty: Optional[Dict[str, Any]] = None
    explainable_decision_map: Optional[Dict[str, Any]] = None
    minimum_diagnostic_test_set: Optional[Dict[str, Any]] = None

# Consultation & Handover Schemas
class ConsultationCreate(BaseModel):
    doctor_id: Optional[int] = None
    symptoms: List[str]
    predicted_disease: Optional[str] = None
    confidence_score: Optional[float] = 0.0
    recommended_tests: Optional[str] = None
    severity: Optional[str] = "Moderate"
    triage_level: Optional[str] = "Doctor Consultation"
    adaptive_qa: Optional[Dict[str, Any]] = {}
    extracted_biomarkers: Optional[Dict[str, Any]] = {}
    xai_reasoning: Optional[List[str]] = []
    patient_notes: Optional[str] = None

class MedicineItem(BaseModel):
    name: str
    dosage: str
    timing: str
    duration: str
    instructions: Optional[str] = None

class PrescriptionCreate(BaseModel):
    consultation_id: int
    diagnosis: str
    medicines: List[MedicineItem]
    general_advice: Optional[str] = None
    follow_up_days: Optional[int] = 7

class SafetyCheckRequest(BaseModel):
    consultation_id: int
    medicines: List[MedicineItem]

class PrescriptionOut(BaseModel):
    id: int
    consultation_id: int
    doctor_id: int
    doctor_name: Optional[str] = None
    diagnosis: str
    medicines: List[MedicineItem]
    general_advice: Optional[str] = None
    follow_up_days: int
    safety_alerts: Optional[Dict[str, Any]] = None
    created_at: datetime

class MedicalReportOut(BaseModel):
    id: int
    consultation_id: Optional[int] = None
    patient_id: int
    report_type: str
    original_filename: str
    stored_filename: str
    file_url: str
    extracted_findings: Optional[Dict[str, Any]] = None
    file_sha256: Optional[str] = None
    blockchain_block_hash: Optional[str] = None
    blockchain_block_index: Optional[int] = None
    verification_status: Optional[str] = "VERIFIED_ON_BLOCKCHAIN"
    uploaded_at: datetime

class RecoveryCheckInCreate(BaseModel):
    consultation_id: int
    day_number: int
    symptom_status: str  # "Significantly Improved", "Improving", "Same", "Worsened"
    current_temperature: Optional[str] = None
    reported_symptoms: Optional[str] = None
    patient_notes: Optional[str] = None

class RecoveryCheckInOut(BaseModel):
    id: int
    consultation_id: int
    patient_id: int
    day_number: int
    symptom_status: str
    current_temperature: Optional[str] = None
    reported_symptoms: Optional[str] = None
    patient_notes: Optional[str] = None
    ai_feedback: Optional[str] = None
    created_at: datetime

class ConsultationOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    patient_allergies: Optional[str] = None
    patient_conditions: Optional[str] = None
    doctor_id: Optional[int] = None
    doctor_name: Optional[str] = None
    symptoms_list: List[str]
    predicted_disease: Optional[str] = None
    confidence_score: Optional[float] = None
    recommended_tests: Optional[str] = None
    severity: Optional[str] = None
    triage_level: Optional[str] = None
    adaptive_qa: Optional[Dict[str, Any]] = None
    extracted_biomarkers: Optional[Dict[str, Any]] = None
    xai_reasoning: Optional[List[str]] = None
    clinical_handover_summary: Optional[Dict[str, Any]] = None
    patient_notes: Optional[str] = None
    status: str
    created_at: datetime
    reports: List[MedicalReportOut] = []
    prescription: Optional[PrescriptionOut] = None
    recovery_checkins: List[RecoveryCheckInOut] = []

# ========================================================
# Closed-Loop Clinical Decision & Verification Schemas
# ========================================================

class UncertaintyAssessmentRequest(BaseModel):
    symptoms: List[str]
    qa_answers: Optional[Dict[str, Any]] = {}
    uploaded_report_ids: Optional[List[int]] = []

class NextQuestionRequest(BaseModel):
    symptoms: List[str]
    answered_question_ids: List[str] = []
    qa_answers: Optional[Dict[str, Any]] = {}

class MinimumTestOptimizationRequest(BaseModel):
    top_disease: str
    top_candidates: List[Dict[str, Any]] = []
    current_uncertainty: float = 60.0
    symptoms: List[str] = []
    triage_level: str = "Doctor Consultation"

class ClinicalDisagreementCreate(BaseModel):
    consultation_id: Optional[int] = None
    patient_id: int
    ai_predicted_disease: str
    ai_confidence: float
    ai_triage_level: str
    doctor_diagnosed_disease: str
    doctor_triage_level: str
    discrepancy_category: str
    doctor_rationale: str
    tests_considered: Optional[List[str]] = []

class ClinicalOutcomeCreate(BaseModel):
    consultation_id: Optional[int] = None
    patient_id: int
    ai_predicted_disease: str
    doctor_diagnosed_disease: str
    confirmed_outcome_disease: str
    confirmation_method: str = "Laboratory / Radiology Report"
    days_to_resolution: int = 5
    outcome_status: str = "Resolved"

class TimelineEntryCreate(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = {}
    severity_level: Optional[str] = "Normal"

class ContextualTokenRequest(BaseModel):
    context_scope: str = "PUBLIC_BASIC" # PUBLIC_BASIC, AMBULANCE_PARAMEDIC, HOSPITAL_ER_TRAUMA

class ExplainableMapRequest(BaseModel):
    target_disease: str
    symptoms: List[str] = []
    qa_answers: Optional[Dict[str, Any]] = {}
