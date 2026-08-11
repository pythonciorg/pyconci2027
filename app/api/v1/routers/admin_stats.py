from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketStatus
from app.models.ticket_category import TicketCategory
from app.models.order import Order
from app.models.room import Room
from app.schemas.stats import DashboardStats, CategoryStat

router = APIRouter(prefix="/admin/stats", tags=["Admin - Statistiques"])


@router.get("/", response_model=DashboardStats)
async def get_dashboard_stats(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()

    total_valid = (
        await db.execute(select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.valid))
    ).scalar_one()

    total_cancelled = (
        await db.execute(select(func.count(Ticket.id)).where(Ticket.status == TicketStatus.cancelled))
    ).scalar_one()

    total_rooms_capacity = (await db.execute(select(func.sum(Room.capacity)))).scalar_one() or 0

    categories_result = await db.execute(select(TicketCategory))
    categories = categories_result.scalars().all()

    category_stats = []
    for cat in categories:
        sold_count = (
            await db.execute(
                select(func.count(Ticket.id))
                .join(Order, Ticket.order_id == Order.id)
                .where(Order.ticket_category_id == cat.id, Ticket.status != TicketStatus.cancelled)
            )
        ).scalar_one()

        fill_rate = round((sold_count / cat.quota) * 100, 1) if cat.quota > 0 else 0.0

        category_stats.append(
            CategoryStat(
                category_id=cat.id,
                name=cat.name,
                quota=cat.quota,
                sold=sold_count,
                fill_rate=fill_rate,
            )
        )

    return DashboardStats(
        total_users=total_users,
        total_tickets_valid=total_valid,
        total_tickets_cancelled=total_cancelled,
        total_rooms_capacity=total_rooms_capacity,
        categories=category_stats,
    )