from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="room")
