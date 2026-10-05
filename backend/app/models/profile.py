from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DomainProfile(Base):
    __tablename__ = "domain_profile"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    name: Mapped[str] = mapped_column(String(128))
    domain: Mapped[str] = mapped_column(String(32))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    voice_style: Mapped[str] = mapped_column(String(32), default="conversational")
    languages: Mapped[List[str]] = mapped_column(JSON, default=list)
    identity: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    knowledge_base: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    intent_map: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    booking_workflow: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    escalation: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    notification_templates: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), index=True, nullable=True)


class RoomType(Base):
    __tablename__ = "room_type"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    profile_id: Mapped[int] = mapped_column(ForeignKey("domain_profile.id"), index=True)
    name: Mapped[str] = mapped_column(String(64))
    calendar_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
