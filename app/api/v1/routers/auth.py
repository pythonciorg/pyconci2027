from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.core.limiter import limiter
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenSchema, UserCreate, UserLogin, UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/register",
    response_model=UserRead,
    summary="Créer un compte utilisateur",
    description="Crée un nouveau compte avec le rôle 'participant' par défaut. "
                "L'email doit être unique. Le mot de passe est haché avant stockage.",
    response_description="Les informations du compte créé (sans le mot de passe).",
)
@limiter.limit("5/minute")
async def register(request: Request, user_in: UserCreate, db: AsyncSession = Depends(get_db)):
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


@router.post(
    "/login",
    response_model=TokenSchema,
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur avec son email et son mot de passe, "
                "et renvoie un access_token (courte durée) et un refresh_token (longue durée).",
    response_description="Les tokens JWT permettant d'accéder aux routes protégées.",
)
@limiter.limit("5/minute")
async def login(request: Request, credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(User).filter_by(email=credentials.email))
    user = query.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    return TokenSchema(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/refresh",
    response_model=TokenSchema,
    summary="Renouveler les tokens",
    description="Génère une nouvelle paire de tokens (access + refresh) à partir d'un "
                "refresh_token valide, sans nécessiter de ressaisir le mot de passe.",
    response_description="Une nouvelle paire de tokens JWT.",
)
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


@router.get(
    "/me",
    response_model=UserRead,
    summary="Profil de l'utilisateur connecté",
    description="Renvoie les informations du compte associé au token d'accès fourni.",
    response_description="Les informations du compte actuellement authentifié.",
)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user