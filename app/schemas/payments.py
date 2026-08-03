from pydantic import BaseModel, EmailStr


class PaymentCreateRequest(BaseModel):
    order_id: int
    success_url: str
    error_url: str


class PaymentStatusRead(BaseModel):
    reference: str
    status: str
    amount: float
    currency: str
    checkout_url: str | None = None


class WebhookEvent(BaseModel):
    event: str
    data: dict
    timestamp: str
