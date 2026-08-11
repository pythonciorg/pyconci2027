from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.article import ArticleStatus


class ArticleBase(BaseModel):
    title: str
    slug: str
    content: str
    excerpt: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None


class ArticleCreate(ArticleBase):
    status: ArticleStatus = ArticleStatus.draft


class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    content: Optional[str] = None
    excerpt: Optional[str] = None
    cover_image_url: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: Optional[ArticleStatus] = None


class Article(ArticleBase):
    id: int
    status: ArticleStatus
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True