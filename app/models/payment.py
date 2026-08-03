from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class PaymentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"
    refunded = "refunded"


class PaymentMethod(str, Enum):
    card = "card"
    mobile_money = "mobile_money"
    unknown = "unknown"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False, index=True)
    geniuspay_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    geniuspay_reference: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    fee: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    net_amount: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[PaymentStatus] = mapped_column(SAEnum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    method: Mapped[PaymentMethod] = mapped_column(SAEnum(PaymentMethod), nullable=False, default=PaymentMethod.unknown)
    environment: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_webhook_payload: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    order: Mapped["Order"] = relationship("Order", back_populates="payments")
