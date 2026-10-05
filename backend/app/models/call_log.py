from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class CallLog(Base):
    __tablename__ = "call_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("domain_profile.id"), index=True)
    vapi_call_id: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_s: Mapped[int] = mapped_column(Integer, default=0)
    caller_phone_masked: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    detected_intents: Mapped[List[str]] = mapped_column(JSON, default=list)
    outcome: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    sentiment: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    urgency_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    recording_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    escalation_target: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(primary_key=True)
    call_log_id: Mapped[int] = mapped_column(ForeignKey("call_log.id"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
