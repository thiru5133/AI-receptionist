from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import CallLog, User

router = APIRouter(prefix="/calls", tags=["calls"])


class CallLogOut(BaseModel):
    id: int
    profile_id: int
    started_at: datetime
    ended_at: Optional[datetime]
    duration_s: int
    caller_phone_masked: Optional[str]
    language: Optional[str]
    detected_intents: List[str]
    outcome: Optional[str]
    sentiment: Optional[str]
    urgency_flag: bool
    recording_url: Optional[str]
    escalation_target: Optional[str]

    class Config:
        from_attributes = True


class CallLogDetail(CallLogOut):
    transcript: Optional[str]


@router.get("", response_model=List[CallLogOut])
def list_calls(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(CallLog)
        .filter(CallLog.tenant_id == user.tenant_id)
        .order_by(CallLog.started_at.desc())
        .limit(200)
        .all()
    )


@router.get("/{call_id}", response_model=CallLogDetail)
def get_call(call_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = (
        db.query(CallLog)
        .filter(CallLog.id == call_id, CallLog.tenant_id == user.tenant_id)
        .first()
    )
    if not c:
        raise HTTPException(404, "Not found")
    return c
