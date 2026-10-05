from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Caller(Base):
    __tablename__ = "caller"
    __table_args__ = (UniqueConstraint("tenant_id", "phone", name="uq_caller_tenant_phone"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenant.id"), index=True)
    phone: Mapped[str] = mapped_column(String(32), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    vip: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    last_booking_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
