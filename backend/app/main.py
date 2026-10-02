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
    closed_loop_router
)

# Initialize database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Personal Health Navigator & Multimodal Triage System",
    description="Adaptive AI health triage, IoT vitals telemetry, blockchain health ledger, predictive care, indoor hospital navigation, emergency response, and community preventive health system.",
    version="3.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None
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


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AI Personal Health Navigator",
        "version": "2.0.0"
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

