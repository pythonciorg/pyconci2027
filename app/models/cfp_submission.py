from datetime import datetime
from enum import Enum

from sqlalchemy import Column, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class SubmissionStatus(str, Enum):
    submitted = "soumis"
    in_review = "en_revue"
    accepted = "accepté"
    rejected = "refusé"


class SubmissionFormat(str, Enum):
    talk = "talk"
    workshop = "atelier"


class CFPSubmission(Base):
    __tablename__ = "cfp_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    speaker_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(120), nullable=False)
    level: Mapped[str] = mapped_column(String(80), nullable=False)
    format: Mapped[SubmissionFormat] = mapped_column(SAEnum(SubmissionFormat), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(SAEnum(SubmissionStatus), nullable=False, default=SubmissionStatus.submitted)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    speaker: Mapped["User"] = relationship("User", back_populates="submissions")
