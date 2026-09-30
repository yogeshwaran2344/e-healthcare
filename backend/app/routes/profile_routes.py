from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..schemas import UserOut, UserProfileUpdate
from ..auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Personal Health Profile"])

@router.get("", response_model=UserOut)
def get_profile(current_user: User = Depends(get_current_user)):
    """Fetch current user's personal health profile."""
    spec = None
    if current_user.doctor_profile:
        spec = current_user.doctor_profile.specialization

    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        age=current_user.age,
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
    """Update personal health parameters (allergies, medications, conditions)."""
    if req.full_name is not None:
        current_user.full_name = req.full_name.strip()
    if req.phone is not None:
        current_user.phone = req.phone.strip()
    if req.age is not None:
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

    return UserOut(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        role=current_user.role,
        phone=current_user.phone,
        age=current_user.age,
        gender=current_user.gender,
        blood_group=current_user.blood_group,
        pre_existing_conditions=current_user.pre_existing_conditions,
        current_medications=current_user.current_medications,
        drug_allergies=current_user.drug_allergies,
        specialization=spec,
        created_at=current_user.created_at
    )
