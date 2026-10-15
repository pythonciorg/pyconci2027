from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role, get_current_user
from app.db.session import get_db
from app.models.cfp_submission import CFPSubmission, SubmissionStatus
from app.models.user import UserRole
from app.schemas.cfp import CFPSubmissionCreate, CFPSubmissionRead, CFPSubmissionStatusUpdate, CFPSubmissionUpdate
from app.tasks.email_tasks import send_notification_email

router = APIRouter(prefix="/cfp", tags=["CFP"])

REVIEWER_ROLES = (UserRole.admin, UserRole.moderator, UserRole.staff)


@router.post("/submissions", response_model=CFPSubmissionRead)
async def create_submission(
    submission_in: CFPSubmissionCreate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication requise")

    submission = CFPSubmission(
        speaker_id=current_user.id,
        title=submission_in.title,
        description=submission_in.description,
        topic=submission_in.topic,
        level=submission_in.level,
        format=submission_in.format,
    )
    db.add(submission)
    await db.commit()
    await db.refresh(submission)
    return submission


@router.get("/submissions", response_model=list[CFPSubmissionRead])
async def list_submissions(
    status_filter: SubmissionStatus | None = Query(None, alias="status"),
    current_user=Depends(require_role(*REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    query = select(CFPSubmission)
    if status_filter:
        query = query.where(CFPSubmission.status == status_filter)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/submissions/{submission_id}", response_model=CFPSubmissionRead)
async def get_submission(
    submission_id: int,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await db.get(CFPSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soumission introuvable")

    is_owner = submission.speaker_id == current_user.id
    is_reviewer = current_user.role in REVIEWER_ROLES
    if not (is_owner or is_reviewer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    return submission


@router.patch("/submissions/{submission_id}", response_model=CFPSubmissionRead)
async def update_submission(
    submission_id: int,
    submission_in: CFPSubmissionUpdate,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    submission = await db.get(CFPSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soumission introuvable")

    if submission.speaker_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé")

    if submission.status != SubmissionStatus.submitted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Soumission déjà en revue, modification impossible",
        )

    for field, value in submission_in.model_dump(exclude_unset=True).items():
        setattr(submission, field, value)

    await db.commit()
    await db.refresh(submission)
    return submission


@router.patch("/submissions/{submission_id}/status", response_model=CFPSubmissionRead)
async def update_submission_status(
    submission_id: int,
    status_update: CFPSubmissionStatusUpdate,
    background_tasks: BackgroundTasks,
    current_user=Depends(require_role(*REVIEWER_ROLES)),
    db: AsyncSession = Depends(get_db),
):
    submission = await db.get(CFPSubmission, submission_id)
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Soumission introuvable")

    if submission.status == status_update.status:
        return submission

    submission.status = status_update.status
    await db.commit()
    await db.refresh(submission, attribute_names=["speaker"])
    send_notification_email(
        background_tasks,
        recipient=submission.speaker.email,
        subject=f"Statut CFP mis à jour : {submission.status}",
        message=f"Votre proposition '{submission.title}' a changé de statut vers {submission.status}.",
    )
    return submission