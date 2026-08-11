from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.conduct_report import ConductReport
from app.models.user import UserRole
from app.schemas.conduct_report import (
    ConductReportCreate,
    ConductReportPublicResponse,
    ConductReportUpdate,
    ConductReport as ConductReportSchema,
)
from fastapi import Request
from app.core.limiter import limiter
router = APIRouter(prefix="/conduct-reports", tags=["Code de conduite"])


@router.post("/", response_model=ConductReportPublicResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/hour")
async def soumettre_signalement(
    request:Request,
    report_in: ConductReportCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Aucune authentification requise : soumission anonyme ouverte à tous
    report = ConductReport(**report_in.model_dump())
    db.add(report)
    await db.commit()
    return ConductReportPublicResponse()


@router.get("/", response_model=List[ConductReportSchema])
async def lister_signalements(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    result = await db.execute(select(ConductReport).order_by(ConductReport.created_at.desc()))
    return result.scalars().all()


@router.get("/{report_id}", response_model=ConductReportSchema)
async def get_signalement(
    report_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    report = await db.get(ConductReport, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signalement non trouvé")
    return report


@router.put("/{report_id}", response_model=ConductReportSchema)
async def modifier_statut_signalement(
    report_id: int,
    update_in: ConductReportUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    report = await db.get(ConductReport, report_id)
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Signalement non trouvé")

    report.status = update_in.status
    await db.commit()
    await db.refresh(report)
    return report