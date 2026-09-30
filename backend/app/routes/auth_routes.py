from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, DoctorProfile
from ..schemas import UserRegister, UserLogin, Token, UserOut
from ..auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

def format_user_out(user: User) -> UserOut:
    spec = None
    if user.doctor_profile:
        spec = user.doctor_profile.specialization

    return UserOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        phone=user.phone,
        age=user.age,
        gender=user.gender,
        blood_group=user.blood_group,
        pre_existing_conditions=user.pre_existing_conditions,
        current_medications=user.current_medications,
        drug_allergies=user.drug_allergies,
        specialization=spec,
        created_at=user.created_at
    )

@router.post("/register", response_model=Token)
def register(req: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")

    user = User(
        full_name=req.full_name.strip(),
        email=req.email.lower().strip(),
        password_hash=hash_password(req.password),
        role=req.role.lower(),
        phone=req.phone,
        age=req.age,
        gender=req.gender,
        blood_group=req.blood_group,
        pre_existing_conditions=req.pre_existing_conditions,
        current_medications=req.current_medications,
        drug_allergies=req.drug_allergies
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if req.role.lower() == "doctor":
        profile = DoctorProfile(
            user_id=user.id,
            specialization=req.specialization or "General Medicine",
            qualification=req.qualification or "MBBS",
            license_number=req.license_number or f"MED-{user.id:04d}",
            experience_years=req.experience_years or 5
        )
        db.add(profile)
        db.commit()

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(access_token=token, token_type="bearer", user=format_user_out(user))

@router.post("/login", response_model=Token)
def login(req: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email.lower().strip()).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(data={"sub": str(user.id), "role": user.role})
    return Token(access_token=token, token_type="bearer", user=format_user_out(user))

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return format_user_out(current_user)
