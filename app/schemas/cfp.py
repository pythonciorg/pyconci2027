from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class SubmissionStatus(str, Enum):
    submitted = "soumis"
    in_review = "en_revue"
    accepted = "accepté"
    rejected = "refusé"


class SubmissionFormat(str, Enum):
    talk = "talk"
    workshop = "atelier"


class CFPSubmissionCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str = Field(..., max_length=5000)
    topic: str = Field(..., max_length=120)
    level: str = Field(..., max_length=80)
    format: SubmissionFormat


class CFPSubmissionRead(BaseModel):
    id: int
    speaker_id: int
    title: str
    description: str
    topic: str
    level: str
    format: SubmissionFormat
    status: SubmissionStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class CFPSubmissionStatusUpdate(BaseModel):
    status: SubmissionStatus




