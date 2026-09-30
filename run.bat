@echo off
title E-Healthcare Platform Server
echo ======================================================================
echo    Starting E-Healthcare Online Consultation & Prediction Server
echo ======================================================================
echo.

REM Seed database if healthcare.db doesn't exist
if not exist "healthcare.db" (
    echo [INFO] Initializing and seeding database...
    python seed_data.py
    echo.
)

echo [INFO] Starting FastAPI Web Server at http://localhost:8000 ...
echo [INFO] Open your browser and navigate to: http://localhost:8000
echo [INFO] Interactive API Docs available at: http://localhost:8000/docs
echo.
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
pause
