from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import DomainProfile, User

router = APIRouter(prefix="/profiles", tags=["profiles"])


class ProfileOut(BaseModel):
    id: int
    name: str
    domain: str
    active: bool
    voice_style: str
    languages: List[str]
    identity: Dict[str, Any]
    knowledge_base: Dict[str, Any]
    intent_map: Dict[str, Any]
    booking_workflow: Dict[str, Any]
    escalation: Dict[str, Any]
    notification_templates: Dict[str, Any]
    phone_number: Optional[str]

    class Config:
        from_attributes = True


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    active: Optional[bool] = None
    voice_style: Optional[str] = None
    languages: Optional[List[str]] = None
    identity: Optional[Dict[str, Any]] = None
    knowledge_base: Optional[Dict[str, Any]] = None
    intent_map: Optional[Dict[str, Any]] = None
    booking_workflow: Optional[Dict[str, Any]] = None
    escalation: Optional[Dict[str, Any]] = None
    notification_templates: Optional[Dict[str, Any]] = None


@router.get("", response_model=List[ProfileOut])
def list_profiles(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(DomainProfile).filter(DomainProfile.tenant_id == user.tenant_id).all()


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    p = (
        db.query(DomainProfile)
        .filter(DomainProfile.id == profile_id, DomainProfile.tenant_id == user.tenant_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Not found")
    return p


@router.patch("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int,
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    p = (
        db.query(DomainProfile)
        .filter(DomainProfile.id == profile_id, DomainProfile.tenant_id == user.tenant_id)
        .first()
    )
    if not p:
        raise HTTPException(404, "Not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p
