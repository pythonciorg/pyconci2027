from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.translation import Translation
from app.models.user import UserRole
from app.schemas.translation import TranslationCreate, TranslationUpdate, Translation as TranslationSchema

router = APIRouter(prefix="/translations", tags=["Traductions"])


@router.get("/", response_model=List[TranslationSchema])
async def lister_traductions(
    db: Annotated[AsyncSession, Depends(get_db)],
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    language: Optional[str] = None,
):
    query = select(Translation)
    if entity_type is not None:
        query = query.where(Translation.entity_type == entity_type)
    if entity_id is not None:
        query = query.where(Translation.entity_id == entity_id)
    if language is not None:
        query = query.where(Translation.language == language)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/", response_model=TranslationSchema, status_code=status.HTTP_201_CREATED)
async def creer_traduction(
    translation_in: TranslationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    translation = Translation(**translation_in.model_dump())
    db.add(translation)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Une traduction existe déjà pour cette entité/langue/champ",
        )
    await db.refresh(translation)
    return translation


@router.put("/{translation_id}", response_model=TranslationSchema)
async def modifier_traduction(
    translation_id: int,
    update_in: TranslationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    translation = await db.get(Translation, translation_id)
    if not translation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Traduction non trouvée")
    translation.value = update_in.value
    await db.commit()
    await db.refresh(translation)
    return translation


@router.delete("/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_traduction(
    translation_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    translation = await db.get(Translation, translation_id)
    if not translation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Traduction non trouvée")
    await db.delete(translation)
    await db.commit()