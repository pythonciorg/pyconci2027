import uuid

from app.models.order import Order
from app.models.ticket import Ticket, TicketStatus
from sqlalchemy.ext.asyncio import AsyncSession


def generate_ticket_qr_code(order: Order, db: AsyncSession) -> list[Ticket]:
    tickets: list[Ticket] = []
    for _ in range(order.quantity):
        ticket = Ticket(
            order_id=order.id,
            qr_code=str(uuid.uuid4()),
            status=TicketStatus.valid,
        )
        db.add(ticket)
        tickets.append(ticket)
    return tickets


async def create_tickets_for_order(order: Order, db: AsyncSession) -> list[Ticket]:
    tickets = generate_ticket_qr_code(order, db)
    await db.flush()
    return tickets
