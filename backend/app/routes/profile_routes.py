from datetime import datetime
import hashlib
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, FamilyMember
from ..schemas import (
    UserOut, UserProfileUpdate,
    FamilyMemberCreate, FamilyMemberUpdate, FamilyMemberOut, FamilyMemberEmergencyLookupOut
)
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

def generate_family_emergency_hash(user_id: int, full_name: str, blood_group: Optional[str] = None) -> str:
    """Generates a secure, cryptographic SHA-256 Emergency Hash for a family member."""
    seed = f"NC-FAM-{user_id}-{full_name.strip()}-{blood_group or 'UNKNOWN'}-{uuid.uuid4().hex}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()

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


# =========================================================================
# FAMILY MEMBERS & EMERGENCY HASHCODE REGISTRY ENDPOINTS
# =========================================================================

@router.get("/family", response_model=List[FamilyMemberOut])
def get_family_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve list of registered family members and their emergency hashcodes for the user."""
    members = db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).order_by(FamilyMember.id.asc()).all()
    # Update dynamic ages if DOB is stored
    results = []
    for m in members:
        calc_age = compute_age_from_dob(m.date_of_birth) if m.date_of_birth else m.age
        results.append(FamilyMemberOut(
            id=m.id,
            user_id=m.user_id,
            full_name=m.full_name,
            relationship=m.relationship,
            age=calc_age,
            date_of_birth=m.date_of_birth,
            gender=m.gender,
            blood_group=m.blood_group,
            phone=m.phone,
            whatsapp=m.whatsapp,
            known_allergies=m.known_allergies,
            chronic_conditions=m.chronic_conditions,
            current_medications=m.current_medications,
            emergency_hashcode=m.emergency_hashcode,
            notes=m.notes,
            created_at=m.created_at,
            updated_at=m.updated_at
        ))
    return results

@router.post("/family", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED)
def add_family_member(
    req: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register a new family member with emergency details and cryptographic hashcode."""
    if not req.full_name or not req.full_name.strip():
        raise HTTPException(status_code=400, detail="Full name is required.")
    if not req.relationship or not req.relationship.strip():
        raise HTTPException(status_code=400, detail="Relationship is required.")

    # Calculate dynamic age
    calc_age = compute_age_from_dob(req.date_of_birth) if req.date_of_birth else req.age

    # Auto-generate emergency hashcode if not provided or blank
    hashcode = req.emergency_hashcode.strip() if req.emergency_hashcode and req.emergency_hashcode.strip() else None
    if not hashcode:
        hashcode = generate_family_emergency_hash(current_user.id, req.full_name, req.blood_group)

    # Check for hash uniqueness collision (extremely rare with sha256)
    existing_hash = db.query(FamilyMember).filter(FamilyMember.emergency_hashcode == hashcode).first()
    if existing_hash:
        hashcode = generate_family_emergency_hash(current_user.id, req.full_name, req.blood_group)

    member = FamilyMember(
        user_id=current_user.id,
        full_name=req.full_name.strip(),
        relationship=req.relationship.strip(),
        age=calc_age,
        date_of_birth=req.date_of_birth.strip() if req.date_of_birth else None,
        gender=req.gender or "Other",
        blood_group=req.blood_group.strip() if req.blood_group else None,
        phone=req.phone.strip() if req.phone else None,
        whatsapp=req.whatsapp.strip() if req.whatsapp else (req.phone.strip() if req.phone else None),
        known_allergies=req.known_allergies.strip() if req.known_allergies else None,
        chronic_conditions=req.chronic_conditions.strip() if req.chronic_conditions else None,
        current_medications=req.current_medications.strip() if req.current_medications else None,
        emergency_hashcode=hashcode,
        notes=req.notes.strip() if req.notes else None
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return FamilyMemberOut(
        id=member.id,
        user_id=member.user_id,
        full_name=member.full_name,
        relationship=member.relationship,
        age=calc_age,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        blood_group=member.blood_group,
        phone=member.phone,
        whatsapp=member.whatsapp,
        known_allergies=member.known_allergies,
        chronic_conditions=member.chronic_conditions,
        current_medications=member.current_medications,
        emergency_hashcode=member.emergency_hashcode,
        notes=member.notes,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.put("/family/{member_id}", response_model=FamilyMemberOut)
def update_family_member(
    member_id: int,
    req: FamilyMemberUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing family member's details or emergency hashcode."""
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found.")

    if req.full_name is not None:
        member.full_name = req.full_name.strip()
    if req.relationship is not None:
        member.relationship = req.relationship.strip()
    if req.date_of_birth is not None:
        member.date_of_birth = req.date_of_birth.strip()
        calc_age = compute_age_from_dob(member.date_of_birth)
        if calc_age is not None:
            member.age = calc_age
    elif req.age is not None:
        member.age = req.age

    if req.gender is not None:
        member.gender = req.gender
    if req.blood_group is not None:
        member.blood_group = req.blood_group.strip()
    if req.phone is not None:
        member.phone = req.phone.strip()
    if req.whatsapp is not None:
        member.whatsapp = req.whatsapp.strip()
    if req.known_allergies is not None:
        member.known_allergies = req.known_allergies.strip()
    if req.chronic_conditions is not None:
        member.chronic_conditions = req.chronic_conditions.strip()
    if req.current_medications is not None:
        member.current_medications = req.current_medications.strip()
    if req.emergency_hashcode is not None and req.emergency_hashcode.strip():
        member.emergency_hashcode = req.emergency_hashcode.strip()
    if req.notes is not None:
        member.notes = req.notes.strip()

    member.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(member)

    calc_age = compute_age_from_dob(member.date_of_birth) if member.date_of_birth else member.age

    return FamilyMemberOut(
        id=member.id,
        user_id=member.user_id,
        full_name=member.full_name,
        relationship=member.relationship,
        age=calc_age,
        date_of_birth=member.date_of_birth,
        gender=member.gender,
        blood_group=member.blood_group,
        phone=member.phone,
        whatsapp=member.whatsapp,
        known_allergies=member.known_allergies,
        chronic_conditions=member.chronic_conditions,
        current_medications=member.current_medications,
        emergency_hashcode=member.emergency_hashcode,
        notes=member.notes,
        created_at=member.created_at,
        updated_at=member.updated_at
    )

@router.delete("/family/{member_id}")
def delete_family_member(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove a family member from the user's emergency registry."""
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Family member not found.")

    db.delete(member)
    db.commit()
    return {"message": "Family member removed successfully.", "id": member_id}

@router.get("/family/emergency-lookup/{hashcode}", response_model=FamilyMemberEmergencyLookupOut)
def lookup_family_emergency_record(
    hashcode: str,
    db: Session = Depends(get_db)
):
    """Emergency Paramedic / Hospital Triage lookup by Family Member Emergency Hashcode."""
    hash_clean = hashcode.strip()
    member = db.query(FamilyMember).filter(FamilyMember.emergency_hashcode == hash_clean).first()
    if not member:
        raise HTTPException(status_code=404, detail="Emergency hashcode not found or invalid.")

    guardian = db.query(User).filter(User.id == member.user_id).first()
    guardian_name = guardian.full_name if guardian else "Emergency Guardian"
    guardian_phone = guardian.phone if guardian else None

    calc_age = compute_age_from_dob(member.date_of_birth) if member.date_of_birth else member.age

    return FamilyMemberEmergencyLookupOut(
        id=member.id,
        full_name=member.full_name,
        relationship=member.relationship,
        age=calc_age,
        gender=member.gender,
        blood_group=member.blood_group,
        phone=member.phone,
        whatsapp=member.whatsapp,
        known_allergies=member.known_allergies,
        chronic_conditions=member.chronic_conditions,
        current_medications=member.current_medications,
        emergency_hashcode=member.emergency_hashcode,
        notes=member.notes,
        primary_guardian_name=guardian_name,
        primary_guardian_phone=guardian_phone,
        verified_status="CRYPTOGRAPHICALLY_VERIFIED"
    )

