from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TicketStatus(str, Enum):
    valid = "valide"
    used = "utilisé"
    cancelled = "annulé"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    qr_code: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    status: Mapped[TicketStatus] = mapped_column(SAEnum(TicketStatus), nullable=False, default=TicketStatus.valid)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="tickets")
