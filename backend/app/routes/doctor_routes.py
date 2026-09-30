from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DoctorProfile
from ..schemas import DoctorOut

router = APIRouter(prefix="/api/doctors", tags=["Doctors"])

@router.get("", response_model=List[DoctorOut])
def list_doctors(db: Session = Depends(get_db)):
    """Fetch all registered doctors and their specializations for booking consultations."""
    docs = db.query(DoctorProfile).join(User).filter(DoctorProfile.is_available == True).all()
    results = []
    for d in docs:
        results.append(DoctorOut(
            id=d.id,
            user_id=d.user_id,
            full_name=d.user.full_name,
            email=d.user.email,
            specialization=d.specialization,
            qualification=d.qualification,
            license_number=d.license_number,
            experience_years=d.experience_years,
            hospital_affiliation=d.hospital_affiliation,
            bio=d.bio,
            is_available=d.is_available
        ))
    return results
