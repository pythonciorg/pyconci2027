from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_current_user_optional
from app.db.session import get_db
from app.models.order import Order, OrderStatus
from app.models.ticket_category import TicketCategory
from app.models.user import UserRole
from app.schemas.tickets import OrderCreate, OrderRead

router = APIRouter(prefix="/orders", tags=["Orders"])

# Statuts qui ne "bloquent" plus de places : une commande annulée ou dont le
# paiement a échoué libère le quota qu'elle occupait.
INACTIVE_ORDER_STATUSES = (OrderStatus.cancelled, OrderStatus.failed)


@router.post("", response_model=OrderRead)
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    # Verrou de ligne : empêche deux commandes simultanées de lire le même
    # quota "pas encore à jour" et de survendre les dernières places.
    ticket_category = (
        await db.execute(
            select(TicketCategory)
            .where(TicketCategory.id == order_in.ticket_category_id)
            .with_for_update()
        )
    ).scalar_one_or_none()

    if not ticket_category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Catégorie de billet introuvable")

    # Quota déjà pris par les commandes encore actives de cette catégorie
    # (ni annulées, ni en échec de paiement).
    sold_result = await db.execute(
        select(func.coalesce(func.sum(Order.quantity), 0)).where(
            Order.ticket_category_id == ticket_category.id,
            Order.status.notin_(INACTIVE_ORDER_STATUSES),
        )
    )
    already_sold = sold_result.scalar_one()
    remaining = ticket_category.quota - already_sold

    if order_in.quantity > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantité dépasse le quota disponible",
        )

    order = Order(
        # user_id déduit de l'utilisateur connecté (ou None pour un achat sans compte),
        # jamais fourni tel quel par le client pour éviter l'usurpation.
        user_id=current_user.id if current_user else None,
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        customer_phone=order_in.customer_phone,
        ticket_category_id=ticket_category.id,
        quantity=order_in.quantity,
        total_amount=float(ticket_category.price * order_in.quantity),
        status=OrderStatus.pending,  # à adapter si ta valeur par défaut porte un autre nom
    )
    db.add(order)
    # Important : on NE touche PLUS à ticket_category.quota ici.
    # Le quota reste la valeur totale fixe ; le "restant" est toujours recalculé
    # dynamiquement depuis les commandes/tickets réels (cf. tickets.py).
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/{order_id}", response_model=OrderRead)
async def read_order(
    order_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")

    is_owner = order.user_id is not None and order.user_id == current_user.id
    is_staff = current_user.role in (UserRole.admin, UserRole.staff)
    if not (is_owner or is_staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    return order