from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Booking, User

router = APIRouter(prefix="/bookings", tags=["bookings"])


class BookingOut(BaseModel):
    id: int
    profile_id: int
    room_type_id: int
    guest_name: str
    caller_phone_masked: str
    start_ts: datetime
    end_ts: datetime
    status: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[BookingOut])
def list_bookings(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Booking)
        .filter(Booking.tenant_id == user.tenant_id)
        .order_by(Booking.start_ts.desc())
        .limit(200)
        .all()
    )
