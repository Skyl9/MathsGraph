import psycopg
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import logging
from app.core.exceptions import AuthenticationException, ForbiddenException
from app.db.database import get_db
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

logger = logging.getLogger(__name__)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Récupère l'utilisateur actuel à partir du token. Lève une erreur si le token est invalide."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    conn = await get_db()
    cursor = conn.cursor(cursor_factory=psycopg.extras.DictCursor)
    try:
        cursor.execute(
            "SELECT id, username, email, is_active FROM users WHERE username = %s",
            (username,)
        )
        user = cursor.fetchone()
        if user is None:
            raise credentials_exception
        return dict(user)
    finally:
        cursor.close()
        conn.close()


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

    user_role: str = payload.get("role")
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

    user_role: str = payload.get("role")
    if user_role is None or user_role.lower() != "admin" or user_role.lower() != "moderator":
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