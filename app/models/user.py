from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class UserRole(str, Enum):
    admin = "admin"
    moderator = "moderator"
    staff = "staff"
    participant = "participant"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.participant)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    # Code de connexion envoyé par email (stocké haché, à usage unique).
    otp_code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    otp_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    otp_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    submissions: Mapped[list["CFPSubmission"]] = relationship("CFPSubmission", back_populates="speaker", cascade="all, delete-orphan")
    speaker_profile: Mapped[Optional["Speaker"]] = relationship("Speaker", back_populates="user", uselist=False)
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
