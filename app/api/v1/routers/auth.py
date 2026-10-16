import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_otp_token,
    create_password_reset_token,
    create_refresh_token,
    decode_token,
    generate_otp_code,
    get_password_hash,
    hash_otp_code,
    verify_otp_code,
    verify_password,
    verify_password_reset_token,
)
from app.core.limiter import limiter
from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    ForgotPasswordRequest,
    MessageResponse,
    OTPChallenge,
    OTPResend,
    OTPVerify,
    ResetPasswordRequest,
    TokenSchema,
    UserCreate,
    UserLogin,
    UserRead,
)
from app.tasks.email_tasks import send_notification_email

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()

OTP_MAX_ATTEMPTS = 5
OTP_RESEND_COOLDOWN_SECONDS = 60


def _issue_tokens(user: User) -> TokenSchema:
    claims = {"sub": str(user.id), "email": user.email, "role": user.role.value}
    return TokenSchema(access_token=create_access_token(claims), refresh_token=create_refresh_token(claims))


def _clear_otp(user: User) -> None:
    user.otp_code_hash = None
    user.otp_expires_at = None
    user.otp_attempts = 0


async def _send_login_code(user: User, background_tasks: BackgroundTasks, db: AsyncSession) -> OTPChallenge:
    # Un nouveau code remplace le précédent et remet le compteur d'essais à zéro.
    now = datetime.now(timezone.utc)
    code = generate_otp_code()
    user.otp_code_hash = hash_otp_code(code)
    user.otp_expires_at = now + timedelta(minutes=settings.otp_expire_minutes)
    user.otp_attempts = 0
    user.otp_sent_at = now
    await db.commit()
    send_notification_email(
        background_tasks,
        recipient=user.email,
        subject="Votre code de connexion PyCon CI",
        message=(
            f"Votre code de connexion est : {code}\n"
            f"Il expire dans {settings.otp_expire_minutes} minutes et ne peut être utilisé qu'une seule fois.\n"
            "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
        ),
    )
    return OTPChallenge(message="Un code de connexion a été envoyé par email.", otp_token=create_otp_token(user.id))


async def _user_from_otp_token(otp_token: str, db: AsyncSession) -> User | None:
    try:
        token_payload = decode_token(otp_token)
        if token_payload.get("type") != "otp":
            return None
        user_id = int(token_payload["sub"])
    except (ValueError, KeyError):
        return None

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        return None
    return user


@router.post(
    "/register",
    response_model=OTPChallenge,
    summary="Créer un compte utilisateur",
    description="Crée un nouveau compte avec le rôle 'participant' par défaut et envoie un code "
                "à 6 chiffres par email. Renvoie un otp_token à transmettre, avec le code, à "
                "/auth/otp/verify pour obtenir les tokens. L'email doit être unique. "
                "Le mot de passe est haché avant stockage.",
    response_description="Un message confirmant l'envoi du code, et l'otp_token associé.",
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_in: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
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
    return await _send_login_code(user, background_tasks, db)


@router.post(
    "/login",
    response_model=OTPChallenge,
    summary="Connexion utilisateur",
    description="Vérifie l'email et le mot de passe, puis envoie un code à 6 chiffres par email. "
                "Les tokens ne sont pas renvoyés ici : il faut ensuite appeler /auth/otp/verify "
                "avec l'otp_token renvoyé et le code.",
    response_description="Un message confirmant l'envoi du code, et l'otp_token associé.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    credentials: UserLogin,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    query = await db.execute(select(User).filter_by(email=credentials.email))
    user = query.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    return await _send_login_code(user, background_tasks, db)


@router.post(
    "/otp/verify",
    response_model=TokenSchema,
    summary="Valider le code reçu par email",
    description="Vérifie le code à 6 chiffres reçu après l'inscription ou la connexion, avec "
                "l'otp_token renvoyé par /auth/register ou /auth/login, et renvoie un access_token "
                "(courte durée) et un refresh_token (longue durée). Après "
                f"{OTP_MAX_ATTEMPTS} codes faux, le code est annulé et il faut se reconnecter.",
    response_description="Les tokens JWT permettant d'accéder aux routes protégées.",
)
@limiter.limit("5/minute")
async def verify_login_code(request: Request, payload: OTPVerify, db: AsyncSession = Depends(get_db)):
    invalid_code = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Code invalide ou expiré")

    user = await _user_from_otp_token(payload.otp_token, db)
    if not user or not user.otp_code_hash:
        raise invalid_code

    if user.otp_expires_at < datetime.now(timezone.utc) or user.otp_attempts >= OTP_MAX_ATTEMPTS:
        _clear_otp(user)
        await db.commit()
        raise invalid_code

    if not verify_otp_code(payload.code, user.otp_code_hash):
        user.otp_attempts += 1
        await db.commit()
        raise invalid_code

    _clear_otp(user)
    await db.commit()
    return _issue_tokens(user)


@router.post(
    "/otp/resend",
    response_model=OTPChallenge,
    summary="Renvoyer le code par email",
    description="Envoie un nouveau code à 6 chiffres à partir de l'otp_token en cours, sans "
                "redemander l'email ni le mot de passe. L'ancien code est annulé et un nouvel "
                "otp_token est renvoyé : le site doit remplacer celui qu'il garde. "
                f"Il faut attendre {OTP_RESEND_COOLDOWN_SECONDS} secondes entre deux envois (429 sinon, "
                "avec le délai restant dans l'en-tête Retry-After).",
    response_description="Un message confirmant l'envoi du nouveau code, et le nouvel otp_token.",
)
@limiter.limit("3/minute")
async def resend_login_code(
    request: Request,
    payload: OTPResend,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    user = await _user_from_otp_token(payload.otp_token, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Demande expirée, veuillez vous reconnecter",
        )

    if user.otp_sent_at:
        elapsed = (datetime.now(timezone.utc) - user.otp_sent_at).total_seconds()
        wait = math.ceil(OTP_RESEND_COOLDOWN_SECONDS - elapsed)
        if wait > 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Patientez {wait} secondes avant de demander un nouveau code",
                headers={"Retry-After": str(wait)},
            )

    challenge = await _send_login_code(user, background_tasks, db)
    challenge.message = "Un nouveau code a été envoyé par email."
    return challenge


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


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    summary="Demander la réinitialisation du mot de passe",
    description="Envoie par email un lien de réinitialisation valable pendant une durée limitée. "
                "La réponse est identique que l'email corresponde ou non à un compte, "
                "afin de ne pas révéler quels emails sont inscrits.",
    response_description="Un message de confirmation générique.",
)
@limiter.limit("3/minute")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    query = await db.execute(select(User).filter_by(email=payload.email))
    user = query.scalar_one_or_none()
    if user and user.is_active:
        token = create_password_reset_token(user.id, user.hashed_password)
        reset_link = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        send_notification_email(
            background_tasks,
            recipient=user.email,
            subject="Réinitialisation de votre mot de passe PyCon CI",
            message=(
                "Vous avez demandé la réinitialisation de votre mot de passe.\n"
                f"Cliquez sur ce lien pour en choisir un nouveau : {reset_link}\n"
                f"Ce lien expire dans {settings.password_reset_token_expire_minutes} minutes "
                "et ne peut être utilisé qu'une seule fois.\n"
                "Si vous n'êtes pas à l'origine de cette demande, ignorez cet email."
            ),
        )
    return MessageResponse(message="Si un compte existe avec cet email, un lien de réinitialisation a été envoyé.")


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Réinitialiser le mot de passe",
    description="Définit un nouveau mot de passe à partir du token reçu par email. "
                "Le token est à usage unique et expire après une durée limitée.",
    response_description="Un message confirmant la mise à jour du mot de passe.",
)
@limiter.limit("5/minute")
async def reset_password(request: Request, payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    invalid_token = HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Lien de réinitialisation invalide ou expiré")
    try:
        token_payload = decode_token(payload.token)
        if token_payload.get("type") != "reset":
            raise invalid_token
        user_id = int(token_payload["sub"])
    except (ValueError, KeyError):
        raise invalid_token

    user = await db.get(User, user_id)
    if not user or not user.is_active or not verify_password_reset_token(token_payload, user.hashed_password):
        raise invalid_token

    user.hashed_password = get_password_hash(payload.new_password)
    await db.commit()
    return MessageResponse(message="Mot de passe mis à jour avec succès")


@router.get(
    "/me",
    response_model=UserRead,
    summary="Profil de l'utilisateur connecté",
    description="Renvoie les informations du compte associé au token d'accès fourni.",
    response_description="Les informations du compte actuellement authentifié.",
)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user