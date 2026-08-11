from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.sponsor import NiveauSponsor, Sponsor
from app.models.user import UserRole
from app.schemas.sponsor import (
    NiveauSponsorCreate,
    NiveauSponsor as NiveauSponsorSchema,
    SponsorCreate,
    Sponsor as SponsorSchema,
)
from sqlalchemy.orm import selectinload
router = APIRouter(prefix="/sponsors", tags=["Sponsors"])


# --- Niveaux de sponsoring ---

@router.get("/niveaux", response_model=List[NiveauSponsorSchema])
async def lister_niveaux(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(NiveauSponsor))
    return result.scalars().all()


@router.post("/niveaux", response_model=NiveauSponsorSchema, status_code=status.HTTP_201_CREATED)
async def creer_niveau(
    niveau_in: NiveauSponsorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    niveau = NiveauSponsor(**niveau_in.model_dump())
    db.add(niveau)
    await db.commit()
    await db.refresh(niveau)
    return niveau


# --- Sponsors ---

@router.get("/", response_model=List[SponsorSchema])
async def lister_sponsors(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(Sponsor).options(selectinload(Sponsor.niveau)))
    return result.scalars().all()




@router.get("/{sponsor_id}", response_model=SponsorSchema)
async def get_sponsor(sponsor_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Sponsor).options(selectinload(Sponsor.niveau)).where(Sponsor.id == sponsor_id)
    )
    sponsor = result.scalar_one_or_none()
    if not sponsor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor non trouvé")
    return sponsor


@router.post("/", response_model=SponsorSchema, status_code=status.HTTP_201_CREATED)
async def creer_sponsor(
    sponsor_in: SponsorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    sponsor = Sponsor(**sponsor_in.model_dump())
    db.add(sponsor)
    await db.commit()
    await db.refresh(sponsor, attribute_names=["niveau"])
    return sponsor


@router.put("/{sponsor_id}", response_model=SponsorSchema)
async def modifier_sponsor(
    sponsor_id: int,
    sponsor_in: SponsorCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    sponsor = await db.get(Sponsor, sponsor_id)
    if not sponsor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor non trouvé")

    for champ, valeur in sponsor_in.model_dump().items():
        setattr(sponsor, champ, valeur)

    await db.commit()
    await db.refresh(sponsor, attribute_names=["niveau"])
    return sponsor

@router.delete("/{sponsor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def supprimer_sponsor(
    sponsor_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    sponsor = await db.get(Sponsor, sponsor_id)
    if not sponsor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sponsor non trouvé")

    await db.delete(sponsor)
    await db.commit()