from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserProfileUpdate
from ..auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Personal Health Profile"])

def compute_age_from_dob(dob_str: Optional[str]) -> Optional[int]:
    """Dynamically computes the exact age in years based on today's current date vs DOB."""
    if not dob_str:
        return None
    try:
        birth_date = datetime.strptime(str(dob_str).strip()[:10], "%Y-%m-%d").date()
        today = datetime.utcnow().date()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return max(0, age)
    except Exception:
        return None

@router.get("", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Fetch current user's personal health profile with dynamic auto-incrementing age."""
    spec = None
    if current_user.doctor_profile:
        spec = current_user.doctor_profile.specialization

    # Compute dynamic age if date_of_birth is present
    dynamic_age = compute_age_from_dob(current_user.date_of_birth) if current_user.date_of_birth else current_user.age

    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        age=dynamic_age,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender,
        blood_group=current_user.blood_group,
        pre_existing_conditions=current_user.pre_existing_conditions,
        current_medications=current_user.current_medications,
        drug_allergies=current_user.drug_allergies,
        specialization=spec,
        created_at=current_user.created_at
    )

@router.put("", response_model=UserOut)
def update_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update personal health parameters (allergies, medications, conditions, DOB)."""
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip()
    if req.date_of_birth is not None:
        current_user.date_of_birth = req.date_of_birth.strip()
        calculated_age = compute_age_from_dob(current_user.date_of_birth)
        if calculated_age is not None:
            current_user.age = calculated_age
    elif req.age is not None:
        current_user.age = req.age

    if req.gender is not None:
        current_user.gender = req.gender
    if req.blood_group is not None:
        current_user.blood_group = req.blood_group
    if req.pre_existing_conditions is not None:
        current_user.pre_existing_conditions = req.pre_existing_conditions.strip()
    if req.current_medications is not None:
        current_user.current_medications = req.current_medications.strip()
    if req.drug_allergies is not None:
        current_user.drug_allergies = req.drug_allergies.strip()

    db.commit()
    db.refresh(current_user)

    spec = None
    if current_user.doctor_profile:
        spec = current_user.doctor_profile.specialization

    dynamic_age = compute_age_from_dob(current_user.date_of_birth) if current_user.date_of_birth else current_user.age

    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        age=dynamic_age,
        date_of_birth=current_user.date_of_birth,
        gender=current_user.gender,
        blood_group=current_user.blood_group,
        pre_existing_conditions=current_user.pre_existing_conditions,
        current_medications=current_user.current_medications,
        drug_allergies=current_user.drug_allergies,
        specialization=spec,
        created_at=current_user.created_at
    )
