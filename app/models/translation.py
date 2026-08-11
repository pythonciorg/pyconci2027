from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Translation(Base):
    __tablename__ = "translations"
    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", "language", "field", name="uq_translation"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(nullable=False, index=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False)
    field: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)