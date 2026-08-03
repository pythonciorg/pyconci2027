from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenSchema, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).filter_by(email=user_in.email))
    existing = query.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.participant,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
    existing = query.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email déjà utilisé")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=UserRole.participant,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=TokenSchema)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).filter_by(email=credentials.email))
    user = query.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    access_token = create_access_token({"sub": user.id, "email": user.email, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": user.id, "email": user.email, "role": user.role.value})
    return TokenSchema(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenSchema)
async def refresh_token(token: str = Body(..., embed=True)):
    try:
        payload = decode_token(token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        access_token = create_access_token({"sub": payload["sub"], "email": payload["email"], "role": payload["role"]})
        refresh_token = create_refresh_token({"sub": payload["sub"], "email": payload["email"], "role": payload["role"]})
        return TokenSchema(access_token=access_token, refresh_token=refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user
