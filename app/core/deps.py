import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel, OAuthFlowPassword
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import User


logger = logging.getLogger(__name__)


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str):
        super().__init__(flows=OAuthFlowsModel(password=OAuthFlowPassword(tokenUrl=tokenUrl)))

    async def __call__(self, request: Request) -> Optional[str]:
        # 1. On cherche d'abord le token dans les cookies HttpOnly
        token = request.cookies.get("access_token")

        # 2. Plan B : On regarde dans les headers (indispensable pour Swagger UI)
        if not token:
            header_authorization = request.headers.get("Authorization", "")
            scheme, token = get_authorization_scheme_param(header_authorization)
            if scheme.lower() != "bearer":
                token = None

        if not token:
            raise AuthenticationException(detail="Authentification requise : aucun token trouvé.")

        return token


# On remplace l'ancienne stratégie par la nôtre
oauth2_scheme: OAuth2PasswordBearerWithCookie = OAuth2PasswordBearerWithCookie(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db)):
    """Récupère l'utilisateur actuel à partir du token. Lève une erreur si le token est invalide."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username = payload.get("sub")
    if not isinstance(username, str):
        raise credentials_exception

    stmt = select(User).where(User.username == username)
    user = await session.scalar(stmt)
    if user is None:
        raise credentials_exception

    return user


async def get_optional_current_user(request: Request, session: AsyncSession = Depends(get_db)):
    """Récupère l'utilisateur s'il est authentifié, sinon retourne None, sans lever d'erreur."""
    token = request.cookies.get("access_token")
    if not token:
        header_authorization = request.headers.get("Authorization", "")
        scheme, token_header = get_authorization_scheme_param(header_authorization)
        if scheme.lower() == "bearer":
            token = token_header

    if not token:
        return None

    try:
        payload = decode_token(token)
        if not payload:
            return None
        username = str(payload.get("sub", ""))
        if not username:
            return None
    except Exception:
        return None

    stmt = select(User).where(User.username == username)
    user = await session.scalar(stmt)
    return user


async def get_current_active_user(current_user=Depends(get_current_user)):
    """Vérifie si l'utilisateur est actif"""
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def _get_verified_payload(token: str, allowed_roles: Optional[list[str]] = None):
    """Décode le token et valide les privilèges selon les rôles autorisés."""
    payload = decode_token(token)
    if not payload:
        logger.error("Token invalide")
        raise AuthenticationException(detail="Could not validate credentials")

    if allowed_roles:
        user_role = str(payload.get("role", "")).lower()
        if not user_role or user_role not in allowed_roles:
            raise ForbiddenException(detail="The user does not have enough privileges")

    return payload


def get_current_admin_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et vérifie si le rôle est 'admin'."""
    payload = _get_verified_payload(token, ["admin"])
    logger.info("Admin payload verified")
    return payload


def get_current_moderator_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et vérifie si le rôle est 'admin' ou 'moderator'."""
    payload = _get_verified_payload(token, ["admin", "moderator"])
    logger.info("Moderator or admin payload verified")
    return payload


def get_current_user_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et valide l'authentification (tout rôle accepté)."""
    payload = _get_verified_payload(token)
    logger.info("User payload verified")
    return payload
