from datetime import datetime
from pydantic import BaseModel, Field


class RoomCreate(BaseModel):
    name: str = Field(..., max_length=120)
    capacity: int = Field(..., ge=1)


class RoomRead(BaseModel):
    id: int
    name: str
    capacity: int

    model_config = {"from_attributes": True}


class SessionCreate(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=1200)
    room_id: int
    start_at: datetime
    end_at: datetime
    topic: str | None = Field(None, max_length=120)
    level: str | None = Field(None, max_length=80)
    speaker_id: int | None = None


class SessionRead(BaseModel):
    id: int
    title: str
    description: str | None
    room_id: int
    start_at: datetime
    end_at: datetime
    topic: str | None
    level: str | None
    speaker_id: int | None

    model_config = {"from_attributes": True}
