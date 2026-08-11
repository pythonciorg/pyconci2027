from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role, get_current_user
from app.db.session import get_db
from app.models.article import Article, ArticleStatus
from app.models.user import User, UserRole
from app.schemas.article import ArticleCreate, ArticleUpdate, Article as ArticleSchema
from app.services.translation_service import auto_translate_and_store
router = APIRouter(prefix="/articles", tags=["Articles"])


@router.get("/", response_model=List[ArticleSchema])
async def lister_articles(db: Annotated[AsyncSession, Depends(get_db)]):
    # Lecture publique : uniquement les articles publiés
    result = await db.execute(select(Article).where(Article.status == ArticleStatus.published))
    return result.scalars().all()


@router.get("/{slug}", response_model=ArticleSchema)
async def get_article(slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Article).where(Article.slug == slug, Article.status == ArticleStatus.published)
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article non trouvé")
    return article


@router.post("/", response_model=ArticleSchema, status_code=status.HTTP_201_CREATED)
async def creer_article(
    article_in: ArticleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: User = Depends(require_role(UserRole.admin)),
):
    article = Article(**article_in.model_dump(), author_id=user.id)
    db.add(article)
    await db.commit()
    await db.refresh(article)
    await auto_translate_and_store(
        db,
        entity_type="article",
        entity_id=article.id,
        fields={
            "title": article.title,
            "content": article.content,
            "excerpt": article.excerpt or "",
        },
    )
    return article

@router.put("/{article_id}", response_model=ArticleSchema)
async def modifier_article(
    article_id: int,
    article_in: ArticleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article non trouvé")

    update_data = article_in.model_dump(exclude_unset=True)

    if update_data.get("status") == ArticleStatus.published and article.published_at is None:
        update_data["published_at"] = datetime.utcnow()

    for champ, valeur in update_data.items():
        setattr(article, champ, valeur)

    await db.commit()
    await db.refresh(article)
    await auto_translate_and_store(
        db,
        entity_type="article",
        entity_id=article.id,
        fields={
            "title": article.title,
            "slug":article.slug,
            "content": article.content,
            "excerpt": article.excerpt or "",
        },
    )
    return article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_article(
    article_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    article = await db.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Article non trouvé")
    await db.delete(article)
    await db.commit()