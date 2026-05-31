import logging
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2PasswordBearer, OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy import select

from app.core.exceptions import AuthenticationException, ForbiddenException
from app.core.security import decode_token
from app.db.database import AsyncSessionLocal
from app.db.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = logging.getLogger(__name__)


class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(self, tokenUrl: str):
        super().__init__(flows=OAuthFlowsModel(password={"tokenUrl": tokenUrl}))  # type: ignore

    async def __call__(self, request: Request) -> Optional[str]:
        # 1. On cherche d'abord le token dans les cookies HttpOnly
        token = request.cookies.get("access_token")

        # 2. Plan B : On regarde dans les headers (indispensable pour Swagger UI)
        if not token:
            header_authorization: str = request.headers.get("Authorization")  # type: ignore
            scheme, token = get_authorization_scheme_param(header_authorization)
            if scheme.lower() != "bearer":
                token = None

        if not token:
            raise AuthenticationException(detail="Authentification requise : aucun token trouvé.")

        return token


# On remplace l'ancienne stratégie par la nôtre
oauth2_scheme: OAuth2PasswordBearer = OAuth2PasswordBearerWithCookie(tokenUrl="token")  # type: ignore


async def get_current_user(token: str = Depends(oauth2_scheme), session=Depends(AsyncSessionLocal)):
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


async def get_current_active_user(current_user=Depends(get_current_user)):
    """Vérifie si l'utilisateur est actif"""
    if not current_user["is_active"]:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_admin_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et vérifie si le rôle est 'admin'."""

    payload = decode_token(token)
    if not payload:
        logger.error("Token invalide")
        # Utilisation de l'exception personnalisée
        raise AuthenticationException(detail="Could not validate credentials")

    user_role: str = payload.get("role")  # type: ignore
    if user_role is None or user_role.lower() != "admin":
        # Utilisation de l'exception personnalisée
        raise ForbiddenException(detail="The user does not have enough privileges")
    logger.info("admin payload verified")
    return payload


def get_current_moderator_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et vérifie si le rôle est 'admin'."""

    payload = decode_token(token)
    if not payload:
        logger.error("Token invalide")
        # Utilisation de l'exception personnalisée
        raise AuthenticationException(detail="Could not validate credentials")

    user_role: str = payload.get("role")  # type: ignore
    if user_role is None or user_role.lower() not in ["admin", "moderator"]:
        # Utilisation de l'exception personnalisée
        raise ForbiddenException(detail="The user does not have enough privileges")
    logger.info("Moderator or admin payload verified")
    return payload


def get_current_user_payload(token: str = Depends(oauth2_scheme)):
    """Décode le token et vérifie si le rôle est 'admin'."""

    payload = decode_token(token)
    if not payload:
        logger.error("Token invalide")
        # Utilisation de l'exception personnalisée
        raise AuthenticationException(detail="Could not validate credentials")
    logger.info("User payload verified")
    return payload
