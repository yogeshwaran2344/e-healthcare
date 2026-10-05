import sys
from app.database import SessionLocal
from app.models import (
    User, DoctorProfile, IoTDevice, IoTVitalReading, ConsentRecord, Consultation, 
    Prescription, QueueToken, MedicalReport, RecoveryCheckIn, PredictiveFollowUp,
    ChronicAlert, BlockchainBlock, EmergencyAlert, CommunityPost, PreventiveChallenge,
    PatientReward, ClinicalTimelineEntry, AdaptiveDiagnosticSession, 
    ClinicalDisagreementRecord, ClinicalOutcomeRecord, ContextualQRToken, EmergencyAccessAudit
)

db = SessionLocal()

# 1. Delete all fake IoT devices and fake readings
db.query(IoTVitalReading).delete()
db.query(IoTDevice).delete()
db.commit()

# 2. Dummy user emails to purge
dummy_emails = [
    'doctor@example.com',
    'rajesh.cardio@example.com',
    'ananya.gp@example.com',
    'patient@example.com'
]

dummy_users = db.query(User).filter(User.email.in_(dummy_emails)).all()
dummy_user_ids = [u.id for u in dummy_users]

if dummy_user_ids:
    print(f"Purging dummy users with IDs: {dummy_user_ids}")
    
    # Clean related child tables
    db.query(EmergencyAccessAudit).filter((EmergencyAccessAudit.patient_id.in_(dummy_user_ids)) | (EmergencyAccessAudit.accessor_id.in_(dummy_user_ids))).delete(synchronize_session=False)
    db.query(ContextualQRToken).filter(ContextualQRToken.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(ClinicalOutcomeRecord).filter(ClinicalOutcomeRecord.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(ClinicalDisagreementRecord).filter((ClinicalDisagreementRecord.patient_id.in_(dummy_user_ids)) | (ClinicalDisagreementRecord.doctor_id.in_(dummy_user_ids))).delete(synchronize_session=False)
    db.query(AdaptiveDiagnosticSession).filter(AdaptiveDiagnosticSession.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(ClinicalTimelineEntry).filter(ClinicalTimelineEntry.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(PatientReward).filter(PatientReward.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(PreventiveChallenge).filter(PreventiveChallenge.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(CommunityPost).filter(CommunityPost.author_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(EmergencyAlert).filter(EmergencyAlert.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(BlockchainBlock).filter(BlockchainBlock.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(ChronicAlert).filter(ChronicAlert.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(PredictiveFollowUp).filter(PredictiveFollowUp.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(ConsentRecord).filter(ConsentRecord.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(QueueToken).filter((QueueToken.patient_id.in_(dummy_user_ids)) | (QueueToken.doctor_id.in_(dummy_user_ids))).delete(synchronize_session=False)
    
    # Consultations and their direct children
    consultations = db.query(Consultation).filter((Consultation.patient_id.in_(dummy_user_ids)) | (Consultation.doctor_id.in_(dummy_user_ids))).all()
    consultation_ids = [c.id for c in consultations]
    
    if consultation_ids:
        db.query(MedicalReport).filter(MedicalReport.consultation_id.in_(consultation_ids)).delete(synchronize_session=False)
        db.query(Prescription).filter(Prescription.consultation_id.in_(consultation_ids)).delete(synchronize_session=False)
        db.query(RecoveryCheckIn).filter(RecoveryCheckIn.consultation_id.in_(consultation_ids)).delete(synchronize_session=False)
        db.query(Consultation).filter(Consultation.id.in_(consultation_ids)).delete(synchronize_session=False)

    db.query(MedicalReport).filter(MedicalReport.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(Prescription).filter(Prescription.doctor_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(RecoveryCheckIn).filter(RecoveryCheckIn.patient_id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.query(DoctorProfile).filter(DoctorProfile.user_id.in_(dummy_user_ids)).delete(synchronize_session=False)

    # Finally delete the users
    db.query(User).filter(User.id.in_(dummy_user_ids)).delete(synchronize_session=False)
    db.commit()

# 3. Configure Dr. Yogeshwaran
doc_yogesh = db.query(User).filter(User.email == 'vmsyogesh@gmail.com').first()
if doc_yogesh:
    doc_yogesh.full_name = "Dr. Yogeshwaran"
    doc_profile = db.query(DoctorProfile).filter(DoctorProfile.user_id == doc_yogesh.id).first()
    if not doc_profile:
        doc_profile = DoctorProfile(
            user_id=doc_yogesh.id,
            specialization="Gastroenterologist & Physician",
            qualification="MBBS, MD (General Medicine / Gastroenterology)",
            license_number="NMC-2024-98104",
            experience_years=10,
            hospital_affiliation="NeuroCare Multi-Specialty Health Center",
            bio="Specialist in digestive health, clinical diagnosis, and internal medicine.",
            is_available=True
        )
        db.add(doc_profile)
    else:
        doc_profile.specialization = "Gastroenterologist & Physician"
        doc_profile.qualification = "MBBS, MD (General Medicine / Gastroenterology)"
        doc_profile.hospital_affiliation = "NeuroCare Multi-Specialty Health Center"
        doc_profile.is_available = True
    db.commit()

print("Database clean complete.")
print("Active Users:", [(u.id, u.full_name, u.email, u.role) for u in db.query(User).all()])
print("Active Doctor Profiles:", [(d.id, d.user_id, d.specialization, d.hospital_affiliation) for d in db.query(DoctorProfile).all()])
print("IoT Devices Count:", db.query(IoTDevice).count())
print("IoTVitalReadings Count:", db.query(IoTVitalReading).count())
