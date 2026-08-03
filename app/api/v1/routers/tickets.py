from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_category import TicketCategory
from app.models.user import UserRole
from app.schemas.tickets import TicketCategoryRead, TicketVerifyResponse

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/categories", response_model=list[TicketCategoryRead])
async def list_ticket_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TicketCategory))
    categories = result.scalars().all()
    return [
        TicketCategoryRead(
            id=category.id,
            name=category.name,
            price=float(category.price),
            currency=category.currency,
            quota=category.quota,
            sale_start=category.sale_start,
            sale_end=category.sale_end,
            remaining_quota=category.quota,
        )
        for category in categories
    ]


@router.get("/{qr_code}/verify", response_model=TicketVerifyResponse)
async def verify_ticket(qr_code: str, db: AsyncSession = Depends(get_db), current_user=Depends(require_role(UserRole.admin, UserRole.staff))):
    query = await db.execute(select(Ticket).filter_by(qr_code=qr_code))
    ticket = query.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billet introuvable")
    if ticket.status != TicketStatus.valid:
        return TicketVerifyResponse(
            ticket_id=ticket.id,
            status=ticket.status.value,
            order_id=ticket.order_id,
            valid=False,
            message="Billet invalide ou déjà utilisé",
        )
    ticket.status = TicketStatus.used
    await db.commit()
    return TicketVerifyResponse(
        ticket_id=ticket.id,
        status=ticket.status.value,
        order_id=ticket.order_id,
        valid=True,
        message="Billet validé avec succès",
    )
