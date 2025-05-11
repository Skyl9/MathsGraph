from datetime import timedelta

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.database import get_db_connection
from app.schemas import UserCreate


class AuthService:
    @staticmethod
    def register_user(user: UserCreate):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifier si l'utilisateur existe déjà
        cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                       (user.username, user.email))
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail="Username ou email déjà utilisé"
            )

        # Hasher le mot de passe
        hashed_password = get_password_hash(user.password)

        # Créer l'utilisateur
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, username, email, is_active
            """,
            (user.username, user.email, hashed_password)
        )
        new_user = cursor.fetchone()
        conn.commit()

        return {
            "id": new_user[0],
            "username": new_user[1],
            "email": new_user[2],
            "is_active": new_user[3]
        }

    @staticmethod
    def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, password_hash FROM users WHERE username = %s",
            (form_data.username,)
        )
        user = cursor.fetchone()

        if not user or not verify_password(form_data.password, user[2]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[1]}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}
