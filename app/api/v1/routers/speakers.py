from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.speaker import Speaker
from app.models.user import UserRole
from app.schemas.speaker import SpeakerCreate, SpeakerUpdate, Speaker as SpeakerSchema
from app.services.translation_service import auto_translate_and_store
router = APIRouter(prefix="/speakers", tags=["Speakers"])


@router.get("/", response_model=List[SpeakerSchema])
async def lister_speakers(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Speaker))
    return result.scalars().all()


@router.get("/{speaker_id}", response_model=SpeakerSchema)
async def get_speaker(speaker_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    speaker = await db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker non trouvé")
    return speaker


@router.post("/", response_model=SpeakerSchema, status_code=status.HTTP_201_CREATED)
async def creer_speaker(
    speaker_in: SpeakerCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    speaker = Speaker(**speaker_in.model_dump())
    db.add(speaker)
    await db.commit()
    await db.refresh(speaker)
    await auto_translate_and_store(
        db,
        entity_type="speaker",
        entity_id=speaker.id,
        fields={
            "bio": speaker.bio or "",
        },
    )
    return speaker


@router.put("/{speaker_id}", response_model=SpeakerSchema)
async def modifier_speaker(
    speaker_id: int,
    speaker_in: SpeakerUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    speaker = await db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker non trouvé")

    for champ, valeur in speaker_in.model_dump(exclude_unset=True).items():
        setattr(speaker, champ, valeur)

    await db.commit()
    await db.refresh(speaker)
    return speaker


@router.delete("/{speaker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_speaker(
    speaker_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    speaker = await db.get(Speaker, speaker_id)
    if not speaker:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Speaker non trouvé")

    await db.delete(speaker)
    await db.commit()