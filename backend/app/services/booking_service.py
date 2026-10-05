from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.models import Booking, DomainProfile, RoomType, WaitlistEntry


def mask_phone(phone: str) -> str:
    if len(phone) <= 4:
        return "***"
    return "***" + phone[-4:]


def find_profile_by_number(db: Session, phone_number: str) -> Optional[DomainProfile]:
    return db.query(DomainProfile).filter(DomainProfile.phone_number == phone_number).first()


def get_room_type_by_name(
    db: Session, tenant_id: int, profile_id: int, name: str
) -> Optional[RoomType]:
    return (
        db.query(RoomType)
        .filter(
            RoomType.tenant_id == tenant_id,
            RoomType.profile_id == profile_id,
            RoomType.name.ilike(name),
        )
        .first()
    )


def has_conflict(db: Session, room_type_id: int, start_ts: datetime, end_ts: datetime) -> bool:
    """FR-04: double-booking prevention. Overlap check on non-cancelled bookings."""
    overlap = (
        db.query(Booking)
        .filter(
            Booking.room_type_id == room_type_id,
            Booking.status != "cancelled",
            and_(Booking.start_ts < end_ts, Booking.end_ts > start_ts),
        )
        .first()
    )
    return overlap is not None


def create_booking(
    db: Session,
    *,
    tenant_id: int,
    profile_id: int,
    room_type_id: int,
    caller_phone: str,
    guest_name: str,
    start_ts: datetime,
    end_ts: datetime,
    calendar_event_id: Optional[str] = None,
) -> Booking:
    b = Booking(
        tenant_id=tenant_id,
        profile_id=profile_id,
        room_type_id=room_type_id,
        caller_phone_masked=mask_phone(caller_phone),
        guest_name=guest_name,
        start_ts=start_ts,
        end_ts=end_ts,
        status="confirmed",
        calendar_event_id=calendar_event_id,
        source="voice",
    )
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


def add_to_waitlist(
    db: Session,
    *,
    tenant_id: int,
    profile_id: int,
    room_type_id: int,
    caller_phone: str,
    guest_name: str,
    window_start: datetime,
    window_end: datetime,
) -> WaitlistEntry:
    w = WaitlistEntry(
        tenant_id=tenant_id,
        profile_id=profile_id,
        room_type_id=room_type_id,
        caller_phone=caller_phone,
        guest_name=guest_name,
        window_start=window_start,
        window_end=window_end,
    )
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


def find_faq_answer(profile: DomainProfile, question: str) -> Optional[str]:
    """FR-03: KB-only, no hallucination. Naive token-overlap match for POC."""
    kb = profile.knowledge_base or {}
    entries: List[Dict[str, Any]] = kb.get("faqs", [])
    q = question.lower()
    best: Optional[Tuple[int, str]] = None
    for e in entries:
        key = str(e.get("question", "")).lower()
        if not key:
            continue
        tokens = set(key.split()) & set(q.split())
        score = len(tokens)
        if score and (best is None or score > best[0]):
            best = (score, str(e.get("answer", "")))
    return best[1] if best else None
