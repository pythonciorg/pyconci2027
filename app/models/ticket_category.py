from datetime import date

from sqlalchemy import Column, Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TicketCategory(Base):
    __tablename__ = "ticket_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="XOF")
    quota: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sale_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    sale_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    orders: Mapped[list["Order"]] = relationship("Order", back_populates="ticket_category")
