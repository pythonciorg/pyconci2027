from datetime import datetime
from enum import Enum

from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ReportStatus(str, Enum):
    new = "new"
    in_review = "in_review"
    resolved = "resolved"
    dismissed = "dismissed"


class ConductReport(Base):
    __tablename__ = "conduct_reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    incident_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[ReportStatus] = mapped_column(default=ReportStatus.new, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)