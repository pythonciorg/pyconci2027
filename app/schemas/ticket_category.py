from datetime import date
from typing import Optional

from pydantic import BaseModel


class TicketCategoryCreate(BaseModel):
    name: str
    price: float
    currency: str = "XOF"
    quota: int
    sale_start: Optional[date] = None
    sale_end: Optional[date] = None


class TicketCategoryUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    quota: Optional[int] = None
    sale_start: Optional[date] = None
    sale_end: Optional[date] = None


class TicketCategory(TicketCategoryCreate):
    id: int

    class Config:
        from_attributes = True