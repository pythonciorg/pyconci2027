import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.payment import Payment, PaymentStatus, PaymentMethod
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_category import TicketCategory
from app.schemas.payments import PaymentCreateRequest, PaymentStatusRead
from app.services.geniuspay_client import GeniusPayClientError, get_geniuspay_client
from app.services.qrcode_service import generate_qr_code
from app.services.ticket_service import create_tickets_for_order
from app.tasks.email_tasks import send_notification_email

settings = get_settings()
router = APIRouter(prefix="/payments", tags=["Payments"])


async def _create_tickets_for_order(order: Order, db: AsyncSession) -> list[Ticket]:
    tickets: list[Ticket] = []
    for _ in range(order.quantity):
        ticket = Ticket(
            order_id=order.id,
            qr_code=str(uuid.uuid4()),
            status=TicketStatus.valid,
        )
        db.add(ticket)
        tickets.append(ticket)
    await db.flush()
    return tickets


@router.post("", response_model=PaymentStatusRead)
async def create_payment(payment_in: PaymentCreateRequest, db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, payment_in.order_id)
    if not order or order.status != OrderStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Commande introuvable ou déjà traitée")

    ticket_category = await db.get(TicketCategory, order.ticket_category_id)
    if not ticket_category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catégorie de billet introuvable")

    payment_client = get_geniuspay_client()
    try:
        response = await payment_client.create_checkout_payment(
            amount=int(order.total_amount),
            currency="XOF",
            description=f"Billet PyCon CI 2027 - {order.quantity} x {ticket_category.name}",
            customer={
                "name": order.customer_name,
                "email": order.customer_email,
                "phone": order.customer_phone,
            },
            success_url=payment_in.success_url,
            error_url=payment_in.error_url,
            metadata={"order_id": order.id},
        )
    except GeniusPayClientError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    payment = Payment(
        order_id=order.id,
        geniuspay_id=response.get("id"),
        geniuspay_reference=response.get("reference"),
        amount=order.total_amount,
        fee=response.get("fees") or 0.0,
        net_amount=response.get("net_amount") or order.total_amount,
        status=PaymentStatus.pending,
        method=PaymentMethod.unknown,
        environment=settings.geniuspay_environment,
    )
    order.payment_reference = payment.geniuspay_reference
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return PaymentStatusRead(
        reference=payment.geniuspay_reference,
        status=payment.status.value,
        amount=float(payment.amount),
        currency="XOF",
        checkout_url=response.get("checkout_url"),
    )


@router.get("/{reference}", response_model=PaymentStatusRead)
async def get_payment_status(reference: str, db: AsyncSession = Depends(get_db)):
    payment = await db.execute(select(Payment).filter_by(geniuspay_reference=reference))
    payment_obj = payment.scalar_one_or_none()
    if not payment_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paiement introuvable")
    return PaymentStatusRead(
        reference=payment_obj.geniuspay_reference,
        status=payment_obj.status.value,
        amount=float(payment_obj.amount),
        currency=payment_obj.environment and "XOF",
        checkout_url=None,
    )


@router.post("/webhook/geniuspay")
async def geniuspay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_signature: str | None = Header(None),
    x_webhook_timestamp: str | None = Header(None),
    x_webhook_event: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
):
    if not x_webhook_signature or not x_webhook_timestamp or not x_webhook_event:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Headers webhook manquants")

    body = await request.body()
    client = get_geniuspay_client()
    if not client.verify_webhook_signature(body, x_webhook_timestamp, x_webhook_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signature webhook invalide")

    payload = await request.json()
    if abs(datetime.utcnow().timestamp() - int(x_webhook_timestamp)) > 300:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Timestamp webhook expiré")

    metadata = payload.get("metadata") or {}
    order_id = metadata.get("order_id")
    if not order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order metadata manquant")

    order = await db.get(Order, int(order_id))
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")

    event_type = x_webhook_event
    if event_type == "payment.success":
        order.status = OrderStatus.paid
        payment = await db.execute(select(Payment).filter_by(order_id=order.id))
        payment_obj = payment.scalar_one_or_none()
        if payment_obj:
            payment_obj.status = PaymentStatus.completed
            payment_obj.completed_at = datetime.utcnow()
        tickets = await create_tickets_for_order(order, db)
        await db.commit()
        await db.refresh(order)
        attachments = []
        for ticket in tickets:
            qr_bytes = generate_qr_code(ticket.qr_code)
            attachments.append({"filename": f"ticket_{ticket.id}.png", "content": qr_bytes})
        background_tasks.add_task(
            send_notification_email,
            order.customer_email,
            "Paiement confirmé",
            "Votre commande a été payée avec succès. Vous recevrez vos e-billets bientôt.",
            attachments,
        )
    elif event_type in {"payment.failed", "payment.expired", "payment.cancelled"}:
        order.status = OrderStatus.failed
        ticket_category = await db.get(TicketCategory, order.ticket_category_id)
        if ticket_category:
            ticket_category.quota += order.quantity
        payment = await db.execute(select(Payment).filter_by(order_id=order.id))
        payment_obj = payment.scalar_one_or_none()
        if payment_obj:
            payment_obj.status = PaymentStatus.failed
            payment_obj.completed_at = datetime.utcnow()
        await db.commit()
    else:
        await db.commit()

    return {"received": True, "event": event_type}
