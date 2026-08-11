from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenPayload

security = HTTPBearer()
# auto_error=False : ne lève pas de 401 si aucun header Authorization n'est fourni,
# renvoie simplement des credentials à None à la place.
optional_security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        token_data = TokenPayload(**payload)
    except Exception as e:
        import traceback
        print("ERREUR AUTH:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    user = await db.get(User, int(token_data.sub))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


async def get_current_user_optional(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(optional_security)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Optional[User]:
    # Aucun header Authorization fourni : achat sans compte, on renvoie None
    # plutôt que de lever une 401.
    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            return None
        token_data = TokenPayload(**payload)
    except Exception:
        # Un token invalide/expiré ne doit pas bloquer un achat sans compte :
        # on dégrade simplement vers "non connecté" plutôt que de lever une erreur.
        return None

    user = await db.get(User, int(token_data.sub))
    if not user or not user.is_active:
        return None
    return user


def require_role(*roles: UserRole):
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return user

    return role_checker