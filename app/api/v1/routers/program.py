from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.deps import require_role
from app.db.session import get_db
from app.models.room import Room
from app.models.session import Session
from app.models.user import UserRole
from app.schemas.program import RoomCreate, RoomRead, SessionCreate, SessionRead
from app.services.translation_service import auto_translate_and_store
router = APIRouter(prefix="/program", tags=["Programme"])


@router.post("/rooms", response_model=RoomRead)
async def create_room(room_in: RoomCreate, db: AsyncSession = Depends(get_db), current_user=Depends(require_role(UserRole.admin, UserRole.staff))):
    existing = await db.execute(select(Room).filter_by(name=room_in.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Salle déjà existante")
    room = Room(name=room_in.name, capacity=room_in.capacity)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return room


@router.post("/sessions", response_model=SessionRead)
async def create_session(session_in: SessionCreate, db: AsyncSession = Depends(get_db), current_user=Depends(require_role(UserRole.admin, UserRole.staff))):
    overlap_query = select(Session).where(
        Session.room_id == session_in.room_id,
        Session.start_at < session_in.end_at,
        Session.end_at > session_in.start_at,
    )
    overlapping = await db.execute(overlap_query)
    if overlapping.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Chevauchement horaire dans la salle")

    session = Session(
        title=session_in.title,
        description=session_in.description,
        room_id=session_in.room_id,
        start_at=session_in.start_at,
        end_at=session_in.end_at,
        topic=session_in.topic,
        level=session_in.level,
        speaker_id=session_in.speaker_id,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    await auto_translate_and_store(
        db,
        entity_type="session",
        entity_id=session.id,
        fields={
            "title": session.title,
            "description": session.description or "",
            "topic": session.topic or "",
            "level": session.level or "",
        },
    )
    return session


@router.get("", response_model=list[SessionRead])
async def list_sessions(
    day: str | None = Query(None),
    topic: str | None = Query(None),
    level: str | None = Query(None),
    room_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    query = select(Session)
    if day:
        query = query.where(func.date(Session.start_at) == day)
    if topic:
        query = query.where(Session.topic == topic)
    if level:
        query = query.where(Session.level == level)
    if room_id:
        query = query.where(Session.room_id == room_id)
    result = await db.execute(query)
    return result.scalars().all()
