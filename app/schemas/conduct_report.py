from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr,Field

from app.models.conduct_report import ReportStatus


class ConductReportCreate(BaseModel):
    description: str  = Field(..., min_length=10, max_length=3000)
    contact_email: Optional[EmailStr] = None
    incident_location: Optional[str] =Field(None, max_length=255)


class ConductReportUpdate(BaseModel):
    status: ReportStatus


class ConductReportPublicResponse(BaseModel):
    """Réponse renvoyée après soumission — ne confirme que la réception, rien de plus."""
    message: str = "Signalement reçu. Merci de votre confiance."


class ConductReport(BaseModel):
    id: int
    description: str
    contact_email: Optional[str] = None
    incident_location: Optional[str] = None
    status: ReportStatus
    created_at: datetime

    class Config:
        from_attributes = True