from datetime import date, datetime
from pydantic import BaseModel, Field, EmailStr


class TicketCategoryRead(BaseModel):
    id: int
    name: str
    price: float
    currency: str
    quota: int
    sale_start: date | None
    sale_end: date | None
    remaining_quota: int
    sold: int
    model_config = {"from_attributes": True}


class OrderCreate(BaseModel):
    ticket_category_id: int
    quantity: int = Field(..., gt=0)
    customer_name: str = Field(..., max_length=255)
    customer_email: EmailStr
    customer_phone: str = Field(..., max_length=32)
    user_id: int | None = None


class OrderRead(BaseModel):
    id: int
    user_id: int | None
    ticket_category_id: int
    quantity: int
    total_amount: float
    status: str
    payment_reference: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentCreateResponse(BaseModel):
    checkout_url: str
    payment_reference: str


class TicketVerifyResponse(BaseModel):
    ticket_id: int
    status: str
    order_id: int
    valid: bool
    message: str
