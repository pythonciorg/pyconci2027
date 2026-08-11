from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class OrderStatus(str, Enum):
    pending = "en_attente"
    paid = "payé"
    failed = "échoué"
    cancelled = "annulé"

INACTIVE_ORDER_STATUSES = (OrderStatus.cancelled, OrderStatus.failed)

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(255), nullable=False)
    customer_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    ticket_category_id: Mapped[int] = mapped_column(ForeignKey("ticket_categories.id"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(SAEnum(OrderStatus), nullable=False, default=OrderStatus.pending)
    payment_reference: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user: Mapped[Optional["User"]] = relationship("User", back_populates="orders")
    ticket_category: Mapped["TicketCategory"] = relationship("TicketCategory", back_populates="orders")
    tickets: Mapped[list["Ticket"]] = relationship("Ticket", back_populates="order", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
