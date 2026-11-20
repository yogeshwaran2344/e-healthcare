import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .database import engine, Base
from .config import PROJECT_ROOT, UPLOAD_DIR
from .routes import (
    auth_router,
    prediction_router,
    doctor_router,
    consultation_router,
    report_router,
    prescription_router,
    navigator_router,
    profile_router,
    recovery_router,
    predictive_router,
    iot_router,
    blockchain_router,
    queue_navigation_router,
    emergency_router,
    community_preventive_router,
    closed_loop_router,
    contact_router,
    notification_router
)

# Initialize database tables
Base.metadata.create_all(bind=engine)


def migrate_schema_columns():
    """Safely adds newly introduced columns to existing SQLite/PostgreSQL tables at import/startup."""
    try:
        from sqlalchemy import text, inspect
        insp = inspect(engine)
        tables = set(insp.get_table_names())
        with engine.connect() as conn:
            if "users" in tables:
                u_cols = {c["name"] for c in insp.get_columns("users")}
                if "date_of_birth" not in u_cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN date_of_birth VARCHAR(30)"))
                    conn.commit()
            if "medication_schedules" in tables:
                s_cols = {c["name"] for c in insp.get_columns("medication_schedules")}
                if "frequency" not in s_cols:
                    conn.execute(text("ALTER TABLE medication_schedules ADD COLUMN frequency VARCHAR(30) DEFAULT 'daily'"))
                if "target_date" not in s_cols:
                    conn.execute(text("ALTER TABLE medication_schedules ADD COLUMN target_date VARCHAR(20)"))
                if "day_of_week" not in s_cols:
                    conn.execute(text("ALTER TABLE medication_schedules ADD COLUMN day_of_week VARCHAR(20)"))
                conn.commit()
    except Exception as e:
        print(f"Schema migration notice: {e}")


migrate_schema_columns()


def auto_migrate():
    """Ensures newly added columns are automatically migrated into existing database tables and dummy data is purged."""
    migrate_schema_columns()

    # Ensure dummy doctors/patients are purged and Dr. Yogeshwaran is configured
    try:
        from .database import SessionLocal
        from .models import User, DoctorProfile, IoTDevice, IoTVitalReading
        db = SessionLocal()
        dummy_emails = ['doctor@example.com', 'rajesh.cardio@example.com', 'ananya.gp@example.com', 'patient@example.com']
        dummy_users = db.query(User).filter(User.email.in_(dummy_emails)).all()
        if dummy_users:
            dummy_ids = [u.id for u in dummy_users]
            db.query(DoctorProfile).filter(DoctorProfile.user_id.in_(dummy_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(dummy_ids)).delete(synchronize_session=False)
            db.commit()

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

        # Sync any dummy placeholder phone numbers on active user and caretaker records to DEFAULT_ALERT_RECIPIENT
        from .models import CaretakerAlertConfig, MedicationSchedule
        from .sms_service import resolve_valid_recipient_phone, DUMMY_PLACEHOLDER_NUMBERS, sanitize_indian_mobile_number
        default_phone = f"+91{resolve_valid_recipient_phone('')}"
        for u in db.query(User).all():
            if not u.phone or sanitize_indian_mobile_number(u.phone) in DUMMY_PLACEHOLDER_NUMBERS:
                u.phone = default_phone
            if not u.emergency_contact_phone or sanitize_indian_mobile_number(u.emergency_contact_phone) in DUMMY_PLACEHOLDER_NUMBERS:
                u.emergency_contact_phone = default_phone
        for cfg in db.query(CaretakerAlertConfig).all():
            if not cfg.caretaker_phone or sanitize_indian_mobile_number(cfg.caretaker_phone) in DUMMY_PLACEHOLDER_NUMBERS:
                cfg.caretaker_phone = default_phone
            if cfg.secondary_phone and sanitize_indian_mobile_number(cfg.secondary_phone) in DUMMY_PLACEHOLDER_NUMBERS:
                cfg.secondary_phone = default_phone
        for ms in db.query(MedicationSchedule).all():
            if not ms.patient_phone or sanitize_indian_mobile_number(ms.patient_phone) in DUMMY_PLACEHOLDER_NUMBERS:
                ms.patient_phone = default_phone
        db.commit()
        db.close()
    except Exception as e:
        print(f"Startup clean/doctor sync notice: {e}")

auto_migrate()

from contextlib import asynccontextmanager
from .medication_reminders import start_medication_scheduler, stop_medication_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Launch background medication schedule monitoring worker
    scheduler = start_medication_scheduler(interval_seconds=60)
    yield
    # Shutdown: Gracefully stop background worker
    stop_medication_scheduler()

app = FastAPI(
    title="NeuroCare | Intelligent Health Passport & Medical Platform",
    description="Adaptive AI health triage, IoT vitals telemetry, blockchain health ledger, predictive care, indoor hospital navigation, emergency response, and automated reminders.",
    version="3.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth_router)
app.include_router(prediction_router)
app.include_router(doctor_router)
app.include_router(consultation_router)
app.include_router(report_router)
app.include_router(prescription_router)
app.include_router(navigator_router)
app.include_router(profile_router)
app.include_router(recovery_router)
app.include_router(predictive_router)
app.include_router(iot_router)
app.include_router(blockchain_router)
app.include_router(queue_navigation_router)
app.include_router(emergency_router)
app.include_router(community_preventive_router)
app.include_router(closed_loop_router)
app.include_router(contact_router)
app.include_router(notification_router)



@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "NeuroCare Health Navigator",
        "version": "3.0.0"
    }

# Mount frontend directory
frontend_dir = os.path.join(PROJECT_ROOT, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def serve_index():
    index_path = os.path.join(PROJECT_ROOT, "frontend", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "AI Personal Health Navigator is active. Visit /docs for API Explorer."}

@app.get("/patient")
def serve_patient():
    patient_path = os.path.join(PROJECT_ROOT, "frontend", "patient.html")
    if os.path.exists(patient_path):
        return FileResponse(patient_path)
    return {"message": "Patient Navigator Dashboard"}

@app.get("/doctor")
def serve_doctor():
    doctor_path = os.path.join(PROJECT_ROOT, "frontend", "doctor.html")
    if os.path.exists(doctor_path):
        return FileResponse(doctor_path)
    return {"message": "Doctor Clinical Handover Portal"}

@app.get("/hospital")
def serve_hospital():
    hospital_path = os.path.join(PROJECT_ROOT, "frontend", "hospital.html")
    if os.path.exists(hospital_path):
        return FileResponse(hospital_path)
    return {"message": "Hospital & Institution Portal"}

@app.get("/emergency/view")
def serve_emergency_view():
    emergency_path = os.path.join(PROJECT_ROOT, "frontend", "emergency.html")
    if os.path.exists(emergency_path):
        return FileResponse(emergency_path)
    return {"message": "Emergency Medical Passport"}

