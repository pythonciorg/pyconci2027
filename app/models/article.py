from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class ArticleStatus(str, Enum):
    draft = "draft"
    published = "published"


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str | None] = mapped_column(String(500), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Champs SEO
    meta_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[str | None] = mapped_column(String(300), nullable=True)

    status: Mapped[ArticleStatus] = mapped_column(default=ArticleStatus.draft, nullable=False)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    author: Mapped[Optional["User"]] = relationship("User")