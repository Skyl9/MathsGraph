import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au hash"""
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """Génère un hash pour le mot de passe (avec hashlib + sha256)"""
    # Vous pouvez ajouter un "sel" fixe ou dynamique pour renforcer le mot de passe
    salt = settings.PASSWORD_SALT.encode("utf-8")  # Assurez-vous que le sel est défini dans les settings
    return hashlib.sha256(salt + password.encode("utf-8")).hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT"""
    to_encode = data.copy()
    now = datetime.now(timezone.utc)  # Obtenez un datetime avec timezone UTC
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Décode un token JWT"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
