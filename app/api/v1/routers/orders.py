from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.ticket_category import TicketCategory
from app.schemas.tickets import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderRead)
async def create_order(order_in: OrderCreate, db: AsyncSession = Depends(get_db)):
    ticket_category = await db.get(TicketCategory, order_in.ticket_category_id)
    if not ticket_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie de billet introuvable")

    total_ordered = order_in.quantity
    if total_ordered > ticket_category.quota:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quantité dépasse le quota disponible")

    order = Order(
        user_id=order_in.user_id,
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        customer_phone=order_in.customer_phone,
        ticket_category_id=ticket_category.id,
        quantity=order_in.quantity,
        total_amount=float(ticket_category.price * order_in.quantity),
    )
    db.add(order)
    ticket_category.quota = ticket_category.quota - order_in.quantity
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(order_id: int, current_user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")
    return order
