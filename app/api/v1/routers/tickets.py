from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_category import TicketCategory
from app.models.order import Order, OrderStatus, INACTIVE_ORDER_STATUSES
from app.models.user import UserRole
from app.schemas.tickets import TicketCategoryRead, TicketVerifyResponse
from app.schemas.ticket_category import (
    TicketCategoryCreate,
    TicketCategoryUpdate,
    TicketCategory as TicketCategorySchema,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/categories", response_model=list[TicketCategoryRead])
async def list_ticket_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TicketCategory))
    categories = result.scalars().all()

    # Quota déjà réservé par les commandes actives (ni annulées, ni en échec) —
    # même logique que dans orders.py, pour que les deux endpoints s'accordent.
    reserved_result = await db.execute(
        select(Order.ticket_category_id, func.coalesce(func.sum(Order.quantity), 0))
        .where(Order.status.notin_(INACTIVE_ORDER_STATUSES))
        .group_by(Order.ticket_category_id)
    )
    reserved_map = dict(reserved_result.all())

    # Billets réellement émis après paiement confirmé — statistique informative,
    # distincte du calcul du restant.
    sold_result = await db.execute(
        select(Order.ticket_category_id, func.count(Ticket.id))
        .join(Order, Ticket.order_id == Order.id)
        .where(
            Ticket.status != TicketStatus.cancelled,
            Order.status.notin_(INACTIVE_ORDER_STATUSES),
        )
        .group_by(Order.ticket_category_id)
    )
    sold_map = dict(sold_result.all())

    return [
        TicketCategoryRead(
            id=category.id,
            name=category.name,
            price=float(category.price),
            currency=category.currency,
            quota=category.quota,
            sale_start=category.sale_start,
            sale_end=category.sale_end,
            remaining_quota=max(category.quota - reserved_map.get(category.id, 0), 0),
            sold=sold_map.get(category.id, 0),
        )
        for category in categories
    ]


@router.get("/{qr_code}/verify", response_model=TicketVerifyResponse)
async def verify_ticket(
    qr_code: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_role(UserRole.admin, UserRole.staff)),
):
    # UPDATE atomique : ne passe à "used" QUE si le statut est encore "valid".
    # Évite la race condition en cas de double-scan simultané du même billet.
    result = await db.execute(
        update(Ticket)
        .where(Ticket.qr_code == qr_code, Ticket.status == TicketStatus.valid)
        .values(status=TicketStatus.used)
        .returning(Ticket)
    )
    ticket = result.scalar_one_or_none()

    if ticket:
        await db.commit()
        return TicketVerifyResponse(
            ticket_id=ticket.id,
            status=ticket.status.value,
            order_id=ticket.order_id,
            valid=True,
            message="Billet validé avec succès",
        )

    await db.rollback()
    query = await db.execute(select(Ticket).filter_by(qr_code=qr_code))
    existing_ticket = query.scalar_one_or_none()

    if not existing_ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Billet introuvable")

    return TicketVerifyResponse(
        ticket_id=existing_ticket.id,
        status=existing_ticket.status.value,
        order_id=existing_ticket.order_id,
        valid=False,
        message="Billet invalide ou déjà utilisé",
    )


@router.post("/categories", response_model=TicketCategorySchema, status_code=status.HTTP_201_CREATED)
async def creer_categorie(
    categorie_in: TicketCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    categorie = TicketCategory(**categorie_in.model_dump())
    db.add(categorie)
    await db.commit()
    await db.refresh(categorie)
    return categorie


@router.put("/categories/{category_id}", response_model=TicketCategorySchema)
async def modifier_categorie(
    category_id: int,
    categorie_in: TicketCategoryUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    categorie = await db.get(TicketCategory, category_id)
    if not categorie:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie non trouvée")

    for champ, valeur in categorie_in.model_dump(exclude_unset=True).items():
        setattr(categorie, champ, valeur)

    await db.commit()
    await db.refresh(categorie)
    return categorie