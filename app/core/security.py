from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
import bcrypt

from app.core.config import settings
from app.schemas.TokenType import TokenPayload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe en clair correspond au hash bcrypt."""
    try:
        # bcrypt.checkpw compare le mot de passe en clair (encodé en bytes)
        # avec le hash (encodé en bytes) et gère le sel automatiquement.
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except ValueError:
        # Si le hash stocké n'est pas un hash bcrypt valide, bcrypt.checkpw lève une ValueError.
        # Cela peut arriver si vous avez d'anciens hashes SHA256 dans la base de données.
        # Dans un scénario de migration, vous devriez gérer ces anciens hashes ici.
        return False


def get_password_hash(password: str) -> str:
    """Génère un hash pour le mot de passe en utilisant bcrypt."""
    # bcrypt.gensalt() génère un nouveau sel aléatoire à chaque fois, ce qui est une bonne pratique.
    # Le coût (nombre d'itérations) peut être ajusté en passant un paramètre 'rounds' à gensalt().
    # Plus le coût est élevé, plus le hachage est lent et sécurisé, mais consomme plus de CPU.
    hashed_password_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    # Le hash est retourné sous forme de bytes, nous le décodons en chaîne pour le stockage en DB.
    return hashed_password_bytes.decode("utf-8")


def create_access_token(data: TokenPayload, expires_delta: Optional[timedelta] = None) -> str:
    """Crée un token JWT"""
    to_encode = data.model_dump()
    now = datetime.now(timezone.utc)  # Obtenez un datetime avec timezone UTC
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)

    to_encode["exp"] = expire
    encoded_jwt: str = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict | None:
    """Décode un token JWT"""
    try:
        payload: dict = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None
