from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.cfp_submission import CFPSubmission, SubmissionStatus
from app.models.user import UserRole
from app.schemas.cfp import CFPSubmissionRead, CFPSubmissionStatusUpdate

router = APIRouter(prefix="/admin/cfp", tags=["Admin - CFP"])


@router.get("/", response_model=List[CFPSubmissionRead])
async def lister_soumissions_cfp(
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
    status_filter: Optional[SubmissionStatus] = None,
):
    query = select(CFPSubmission)
    if status_filter is not None:
        query = query.where(CFPSubmission.status == status_filter)
    query = query.order_by(CFPSubmission.id.desc())

    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{submission_id}", response_model=CFPSubmissionRead)
async def get_soumission_cfp(
    submission_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    submission = await db.get(CFPSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soumission non trouvée")
    return submission


@router.put("/{submission_id}/status", response_model=CFPSubmissionRead)
async def changer_statut_cfp(
    submission_id: int,
    update_in: CFPSubmissionStatusUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _user=Depends(require_role(UserRole.admin)),
):
    submission = await db.get(CFPSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soumission non trouvée")

    submission.status = update_in.status
    await db.commit()
    await db.refresh(submission)
    return submission