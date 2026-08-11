from typing import Optional

from pydantic import BaseModel


class SpeakerBase(BaseModel):
    name: str
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_links: Optional[str] = None


class SpeakerCreate(SpeakerBase):
    user_id: Optional[int] = None


class SpeakerUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[str] = None
    social_links: Optional[str] = None
    user_id: Optional[int] = None


class Speaker(SpeakerBase):
    id: int
    user_id: Optional[int] = None

    class Config:
        from_attributes = True