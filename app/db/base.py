from app.models.base import Base

# Import all models so they are registered on Base.metadata
from app.models.user import User  # noqa: F401
from app.models.speaker import Speaker  # noqa: F401
from app.models.sponsor import NiveauSponsor, Sponsor  # noqa: F401
from app.models.session import Session  # noqa: F401
from app.models.ticket_category import TicketCategory  # noqa: F401
from app.models.room import Room  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.payment import Payment  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.cfp_submission import CFPSubmission  # noqa: F401
from app.models.article import Article
from app.models.conduct_report import ConductReport
from app.models.translation import Translation

# Metadata import helper for Alembic and tests
metadata = Base.metadata
