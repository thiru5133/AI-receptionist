from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Booking(Base):
    __tablename__ = "booking"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("domain_profile.id"), index=True)
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_type.id"), index=True)
    caller_phone_masked: Mapped[str] = mapped_column(String(32))
    guest_name: Mapped[str] = mapped_column(String(128))
    start_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_ts: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(16), default="confirmed")
    calendar_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(String(16), default="voice")
    recurring_parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WaitlistEntry(Base):
    __tablename__ = "waitlist_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("domain_profile.id"), index=True)
    room_type_id: Mapped[int] = mapped_column(ForeignKey("room_type.id"), index=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    caller_phone: Mapped[str] = mapped_column(String(32))
    guest_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="waiting")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
