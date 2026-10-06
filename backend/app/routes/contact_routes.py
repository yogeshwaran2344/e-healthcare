from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import ContactMessage
from ..schemas import ContactMessageCreate, ContactMessageOut

router = APIRouter(prefix="/api/contact", tags=["Contact & Support"])

@router.post("", response_model=ContactMessageOut, status_code=status.HTTP_201_CREATED)
def submit_contact_message(
    payload: ContactMessageCreate,
    db: Session = Depends(get_db)
):
    """Submits a contact/support inquiry and saves it to the database."""
    if not payload.name or not payload.name.strip():
        raise HTTPException(status_code=400, detail="Name is required.")
    if not payload.email or not payload.email.strip():
        raise HTTPException(status_code=400, detail="Valid email is required.")
    if not payload.message or not payload.message.strip():
        raise HTTPException(status_code=400, detail="Message is required.")

    msg = ContactMessage(
        name=payload.name.strip(),
        email=str(payload.email).strip(),
        phone=payload.phone.strip() if payload.phone else None,
        subject=payload.subject.strip() if payload.subject else "General Inquiry",
        message=payload.message.strip(),
        status="new"
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg

@router.get("", response_model=List[ContactMessageOut])
def list_contact_messages(
    db: Session = Depends(get_db)
):
    """Lists all contact messages (newest first)."""
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()
