import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="patient")  # "patient", "doctor", "admin"
    phone = Column(String(30), nullable=True)
    
    # Personal Health Profile (Context)
    age = Column(Integer, nullable=True)
    date_of_birth = Column(String(30), nullable=True)  # e.g., "1998-05-24"
    gender = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    pre_existing_conditions = Column(Text, nullable=True)  # Comma-separated or JSON: "Diabetes Type 2, Hypertension"
    current_medications = Column(Text, nullable=True)      # e.g., "Metformin 500mg, Amlodipine 5mg"
    drug_allergies = Column(Text, nullable=True)           # e.g., "Penicillin, Sulfa, Aspirin"
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    doctor_profile = relationship("DoctorProfile", back_populates="user", uselist=False)
    patient_consultations = relationship("Consultation", back_populates="patient", foreign_keys="Consultation.patient_id")
    doctor_consultations = relationship("Consultation", back_populates="doctor", foreign_keys="Consultation.doctor_id")
    medical_reports = relationship("MedicalReport", back_populates="patient")
    recovery_checkins = relationship("RecoveryCheckIn", back_populates="patient")

class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    specialization = Column(String(100), nullable=False)
    qualification = Column(String(100), default="MBBS, MD")
    license_number = Column(String(50), nullable=False)
    experience_years = Column(Integer, default=5)
    hospital_affiliation = Column(String(150), default="City General Hospital")
    bio = Column(Text, nullable=True)
    is_available = Column(Boolean, default=True)

    user = relationship("User", back_populates="doctor_profile")

class Consultation(Base):
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    symptoms_list = Column(Text, nullable=False)  # JSON list of symptoms
    predicted_disease = Column(String(150), nullable=True)
    confidence_score = Column(Float, default=0.0)
    recommended_tests = Column(Text, nullable=True)
    
    # Advanced AI Personal Health Navigator Fields
    severity = Column(String(50), default="Moderate")
    triage_level = Column(String(50), default="Doctor Consultation") # "Self-Care", "Doctor Consultation", "Emergency Care"
    adaptive_qa = Column(Text, nullable=True)             # JSON: Questions asked & patient answers (duration, temp, pain 1-10)
    extracted_biomarkers = Column(Text, nullable=True)    # JSON: Biomarkers extracted from uploaded reports
    xai_reasoning = Column(Text, nullable=True)           # JSON: Explainable AI factors & why conditions were considered
    clinical_handover_summary = Column(Text, nullable=True) # SBAR structured handover for attending doctor
    patient_notes = Column(Text, nullable=True)
    
    status = Column(String(30), default="pending")  # pending, in_review, completed, cancelled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_consultations")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_consultations")
    reports = relationship("MedicalReport", back_populates="consultation", cascade="all, delete-orphan")
    prescription = relationship("Prescription", back_populates="consultation", uselist=False, cascade="all, delete-orphan")
    recovery_checkins = relationship("RecoveryCheckIn", back_populates="consultation", cascade="all, delete-orphan")

class MedicalReport(Base):
    __tablename__ = "medical_reports"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    report_type = Column(String(50), nullable=False)  # Blood Test, Chest X-Ray, CT Scan, Ultrasound, etc.
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    extracted_findings = Column(Text, nullable=True)  # JSON: Extracted lab parameters, out of range flags
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation", back_populates="reports")
    patient = relationship("User", back_populates="medical_reports")

class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), unique=True, nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    diagnosis = Column(String(255), nullable=False)
    medicines_json = Column(Text, nullable=False)  # JSON string of medicine items
    general_advice = Column(Text, nullable=True)
    follow_up_days = Column(Integer, default=7)
    safety_alerts = Column(Text, nullable=True)    # JSON: Any drug allergy or interaction warnings flagged
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation", back_populates="prescription")

class RecoveryCheckIn(Base):
    """Longitudinal Recovery & Feedback Monitoring Loop"""
    __tablename__ = "recovery_checkins"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    day_number = Column(Integer, default=1)       # Day 1, Day 3, Day 7
    symptom_status = Column(String(50), default="Improving") # "Significantly Improved", "Improving", "Same", "Worsened"
    current_temperature = Column(String(20), nullable=True)  # e.g., "98.6 F"
    reported_symptoms = Column(Text, nullable=True)
    patient_notes = Column(Text, nullable=True)
    ai_feedback = Column(Text, nullable=True)     # "Recovery on track" or "Worsening detected: visit doctor"
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation", back_populates="recovery_checkins")
    patient = relationship("User", back_populates="recovery_checkins")

# ==========================================
# 1. AI + PREDICTIVE CARE & CHRONIC ALERTS
# ==========================================

class PredictiveFollowUp(Base):
    """Predictive follow-up scheduling recommendation based on deterioration risk"""
    __tablename__ = "predictive_followups"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    risk_score = Column(Float, default=45.0)  # 0 to 100
    urgency_level = Column(String(50), default="Moderate") # Low, Moderate, High, Critical
    suggested_timeline = Column(String(100), default="Within 3 days")
    urgency_rationale = Column(Text, nullable=False)
    recommended_specialist = Column(String(100), default="General Physician")
    suggested_date = Column(String(50), nullable=True)
    status = Column(String(50), default="suggested") # suggested, scheduled, dismissed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")
    consultation = relationship("Consultation")

class ChronicAlert(Base):
    """Proactive AI warning for chronic condition escalation or drug/lifestyle risks"""
    __tablename__ = "chronic_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    condition_name = Column(String(100), nullable=False)  # e.g., "Type 2 Diabetes", "Hypertension"
    trigger_source = Column(String(100), default="AI Multi-Factor Analysis") # vitals_trend, lab_biomarker, symptom_intake
    alert_title = Column(String(200), nullable=False)
    clinical_implication = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=False)
    severity = Column(String(30), default="WARNING") # INFO, WARNING, CRITICAL
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

# ==========================================
# 2. IOT WEARABLES INTEGRATION & VITALS
# ==========================================

class IoTDevice(Base):
    """Connected IoT Medical Wearable Registry"""
    __tablename__ = "iot_devices"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_name = Column(String(150), nullable=False) # e.g. "Omron Platinum BP Monitor", "Dexcom G7 Continuous Glucose"
    device_type = Column(String(50), nullable=False) # bp_monitor, glucose_sensor, ecg_sensor, pulse_oximeter, thermometer
    device_uid = Column(String(100), unique=True, nullable=False)
    firmware_version = Column(String(50), default="v3.2.1")
    battery_level = Column(Integer, default=95)
    connection_status = Column(String(30), default="connected") # connected, streaming, disconnected
    last_sync_at = Column(DateTime, default=datetime.datetime.utcnow)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")
    readings = relationship("IoTVitalReading", back_populates="device", cascade="all, delete-orphan")

class IoTVitalReading(Base):
    """Continuous or periodic vital metric stream from connected wearables"""
    __tablename__ = "iot_vital_readings"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    device_id = Column(Integer, ForeignKey("iot_devices.id"), nullable=False)
    metric_type = Column(String(50), nullable=False) # blood_pressure, glucose, heart_rate, spo2, temperature
    primary_value = Column(Float, nullable=False)    # systolic or glucose mg/dL or bpm or % or deg F
    secondary_value = Column(Float, nullable=True)   # diastolic for BP
    unit = Column(String(20), nullable=False)        # mmHg, mg/dL, bpm, %, °F
    is_anomaly = Column(Boolean, default=False)
    alert_severity = Column(String(30), default="NORMAL") # NORMAL, WARNING, CRITICAL
    alert_message = Column(String(255), nullable=True)
    ecg_waveform_points = Column(Text, nullable=True) # JSON list for live ECG visualization
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    device = relationship("IoTDevice", back_populates="readings")
    patient = relationship("User")

# ==========================================
# 3. BLOCKCHAIN HEALTH RECORDS & SHARING
# ==========================================

class BlockchainBlock(Base):
    """Cryptographic, tamper-evident SHA-256 block ledger for patient health records"""
    __tablename__ = "blockchain_ledger"

    id = Column(Integer, primary_key=True, index=True)
    block_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    record_type = Column(String(50), nullable=False) # GENESIS, CONSULTATION, PRESCRIPTION, LAB_REPORT, CONSENT_GRANT
    record_id = Column(String(100), nullable=False)
    data_payload = Column(Text, nullable=False) # Encrypted or JSON structured medical data
    data_hash = Column(String(64), nullable=False) # SHA-256 hash of payload
    previous_hash = Column(String(64), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    block_hash = Column(String(64), unique=True, nullable=False)
    validator_signature = Column(String(128), nullable=False) # Cryptographic signature
    is_verified = Column(Boolean, default=True)

    patient = relationship("User")

class ConsentRecord(Base):
    """Decentralized Patient-Owned Smart Consent Matrix for sharing medical records"""
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    grantee_name = Column(String(150), nullable=False) # Doctor Name, "Star Health Insurance", "AI Oncology Research"
    grantee_type = Column(String(50), default="doctor") # doctor, insurer, researcher
    grantee_organization = Column(String(150), nullable=True)
    permissions = Column(Text, nullable=False) # JSON: ["diagnoses", "labs", "prescriptions", "vitals"]
    access_token = Column(String(128), unique=True, nullable=False)
    status = Column(String(30), default="active") # active, revoked, expired
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

# ==========================================
# 4. SMART INDOOR NAVIGATION & LIVE QUEUE
# ==========================================

class QueueToken(Base):
    """Live OPD and Emergency Patient Queue token with priority routing"""
    __tablename__ = "queue_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_code = Column(String(20), unique=True, nullable=False) # e.g. "A-101", "EMERG-04"
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department = Column(String(100), default="OPD General Medicine")
    priority_level = Column(String(30), default="NORMAL") # NORMAL, PRIORITY, EMERGENCY_CRITICAL
    status = Column(String(30), default="waiting") # waiting, called, in_consultation, completed, skipped
    queue_number = Column(Integer, default=1)
    estimated_wait_minutes = Column(Integer, default=15)
    called_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

class HospitalWaypoint(Base):
    """Hospital Indoor Navigation POIs and Waypoints"""
    __tablename__ = "hospital_waypoints"

    id = Column(Integer, primary_key=True, index=True)
    floor_level = Column(String(50), default="Ground Floor") # Ground Floor, 1st Floor, 2nd Floor
    code = Column(String(50), unique=True, nullable=False) # e.g. "ENTRANCE", "ER_BAY", "OPD_104", "LAB_PATH"
    name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False) # emergency, opd, lab, radiology, pharmacy, elevator, stairs
    coord_x = Column(Float, nullable=False)
    coord_y = Column(Float, nullable=False)
    description = Column(String(255), nullable=True)
    turn_instructions = Column(Text, nullable=True)

# ==========================================
# 5. EMERGENCY RESPONSE & LIVE AMBULANCE
# ==========================================

class EmergencyAlert(Base):
    """One-tap SOS and automatic critical IoT vitals breach emergency dispatch"""
    __tablename__ = "emergency_alerts"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    emergency_type = Column(String(50), default="SOS_MANUAL") # SOS_MANUAL, IOT_CRITICAL_VITALS, CHEST_PAIN_EMERGENCY
    severity = Column(String(30), default="CRITICAL")
    patient_latitude = Column(Float, default=12.9716)
    patient_longitude = Column(Float, default=77.5946)
    ambulance_unit = Column(String(50), default="ALS-Unit 07 (Cardiac Life Support)")
    paramedic_name = Column(String(100), default="Officer Vikram & EMT Priya")
    paramedic_contact = Column(String(30), default="+91 98111 22233")
    ambulance_lat = Column(Float, default=12.9780)
    ambulance_lng = Column(Float, default=77.5990)
    eta_minutes = Column(Integer, default=7)
    hospital_destination = Column(String(150), default="Apex Multi-Specialty Trauma Center")
    reserved_trauma_bay = Column(String(50), default="ER Trauma Bay 3")
    blood_bank_alert = Column(String(100), default="B+ Cross-match pre-alerted")
    patient_snapshot = Column(Text, nullable=True) # JSON snapshot of allergies, vitals, chronic conditions
    status = Column(String(30), default="dispatched") # dispatched, en_route, arrived_scene, in_transit_er, resolved
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

# ==========================================
# 6. COMMUNITY & PREVENTIVE HEALTH
# ==========================================

class CommunityPost(Base):
    """AI-moderated supportive peer groups for chronic care & preventive health"""
    __tablename__ = "community_posts"

    id = Column(Integer, primary_key=True, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_slug = Column(String(50), nullable=False) # diabetes_warriors, heart_health, mental_wellness, oncology_care
    group_name = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    ai_safety_score = Column(Float, default=95.0) # 0 to 100
    ai_moderation_status = Column(String(30), default="approved") # approved, flagged, rejected
    ai_moderation_notes = Column(Text, nullable=True)
    is_ai_verified = Column(Boolean, default=True) # Badge showing AI evaluated for medical safety
    likes_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    author = relationship("User")

class PreventiveChallenge(Base):
    """Gamified daily and weekly preventive wellness challenges"""
    __tablename__ = "preventive_challenges"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    challenge_key = Column(String(50), nullable=False) # daily_steps, hydration_2500ml, bp_streak_7d, low_sugar
    title = Column(String(150), nullable=False)
    description = Column(String(255), nullable=False)
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    unit = Column(String(30), default="steps")
    streak_days = Column(Integer, default=1)
    points_reward = Column(Integer, default=50)
    is_completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

class PatientReward(Base):
    """Patient loyalty points, wellness badges, and healthcare vouchers"""
    __tablename__ = "patient_rewards"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_points = Column(Integer, default=320)
    tier_level = Column(String(30), default="Gold Vitality")
    badges_json = Column(Text, nullable=True) # JSON list of unlocked badges
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

# ==========================================
# 7. CLOSED-LOOP CLINICAL DECISION & VERIFICATION
# ==========================================

class ClinicalTimelineEntry(Base):
    """Longitudinal continuous patient health timeline tracking events and trends over time"""
    __tablename__ = "clinical_timeline_entries"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), nullable=False) # symptom_report, vital_reading, lab_test, doctor_visit, prescription_issued, outcome_verified
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True) # JSON snapshot of vitals, scores, or values
    severity_level = Column(String(30), default="Normal") # Normal, Mild, Moderate, Critical
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

class AdaptiveDiagnosticSession(Base):
    """Tracks dynamic Shannon-entropy uncertainty reduction across adaptive question iterations"""
    __tablename__ = "adaptive_diagnostic_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    initial_symptoms_json = Column(Text, nullable=False) # JSON list
    initial_entropy = Column(Float, default=3.0)
    current_entropy = Column(Float, default=2.0)
    current_uncertainty_score = Column(Float, default=70.0) # 0-100%
    answered_questions_json = Column(Text, nullable=True) # JSON dict of Q&A
    top_predicted_disease = Column(String(150), nullable=True)
    confidence_score = Column(Float, default=0.0)
    minimum_test_set_json = Column(Text, nullable=True) # Pareto-optimized test recommendation
    session_status = Column(String(30), default="in_progress") # in_progress, completed, escalated_to_doctor
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")

class ClinicalDisagreementRecord(Base):
    """Clinical Disagreement Record: captures divergence between AI prediction and Doctor decision"""
    __tablename__ = "clinical_disagreement_records"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    ai_predicted_disease = Column(String(150), nullable=False)
    ai_confidence = Column(Float, default=0.0)
    ai_triage_level = Column(String(50), default="Doctor Consultation")
    
    doctor_diagnosed_disease = Column(String(150), nullable=False)
    doctor_triage_level = Column(String(50), default="Doctor Consultation")
    discrepancy_category = Column(String(80), default="PHYSICAL_EXAM_OVERRIDE")
    severity_grade = Column(String(50), default="MODERATE_DIAGNOSTIC_DIVERGENCE")
    doctor_rationale = Column(Text, nullable=False)
    tests_considered_json = Column(Text, nullable=True) # JSON list
    reconciliation_status = Column(String(30), default="pending_outcome") # pending_outcome, reconciled
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation")
    patient = relationship("User", foreign_keys=[patient_id])
    doctor = relationship("User", foreign_keys=[doctor_id])

class ClinicalOutcomeRecord(Base):
    """Ground truth clinical outcome verification closing the learning loop"""
    __tablename__ = "clinical_outcome_records"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    ai_predicted_disease = Column(String(150), nullable=False)
    doctor_diagnosed_disease = Column(String(150), nullable=False)
    confirmed_outcome_disease = Column(String(150), nullable=False)
    confirmation_method = Column(String(100), default="Laboratory / Radiology Report")
    days_to_resolution = Column(Integer, default=5)
    
    ai_was_correct = Column(Boolean, default=False)
    doctor_was_correct = Column(Boolean, default=True)
    error_category = Column(String(80), default="NO_ERROR") # NO_ERROR, MISSING_SYMPTOM, INCORRECT_WEIGHTING, INSUFFICIENT_LAB_DATA, ATYPICAL_PRESENTATION
    reconciliation_type = Column(String(80), default="PHYSICIAN_OVERRIDE_SAVED_ACCURACY")
    calibration_feedback = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)

    consultation = relationship("Consultation")
    patient = relationship("User")

class ContextualQRToken(Base):
    """Dynamic context-aware emergency token with role-based access and automatic expiration"""
    __tablename__ = "contextual_qr_tokens"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    context_scope = Column(String(50), default="PUBLIC_BASIC") # PUBLIC_BASIC, AMBULANCE_PARAMEDIC, HOSPITAL_ER_TRAUMA
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False)
    access_count = Column(Integer, default=0)
    last_accessed_at = Column(DateTime, nullable=True)
    access_logs_json = Column(Text, nullable=True) # JSON list of {ip, role, timestamp, user_agent}
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    patient = relationship("User")


class EmergencyAccessAudit(Base):
    """Append-only log of emergency medical passport access events."""
    __tablename__ = "emergency_access_audits"

    id = Column(Integer, primary_key=True, index=True)
    accessor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    accessor_role = Column(String(30), nullable=False)
    accessor_name = Column(String(150), nullable=False)
    patient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    accessed_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    purpose = Column(String(255), nullable=True)
    information_type = Column(String(120), default="emergency_passport")
    is_emergency = Column(Boolean, default=True)
    access_channel = Column(String(50), default="authenticated")
    context_scope = Column(String(50), nullable=True)

    accessor = relationship("User", foreign_keys=[accessor_id])
    patient = relationship("User", foreign_keys=[patient_id])


