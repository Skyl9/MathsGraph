import logging
import secrets
import smtplib
from datetime import timedelta, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException, status
from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import settings
from app.core.exceptions import BadRequestException, AuthenticationException, ConflictException
from app.core.security import get_password_hash, verify_password, create_access_token
from app.db.models import User, PasswordResetToken, UserSession
from app.schemas.auth import PasswordResetConfirmSchema, UserCreate

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, user: UserCreate):
        # Vérifier si l'utilisateur existe déjà
        query = select(User).where((User.username == user.username) | (User.email == user.email))
        result = await self.db.execute(query)
        existing_user = result.scalars().first()

        if existing_user:
            if existing_user.username == user.username:
                raise ConflictException(detail="Ce nom d'utilisateur est déjà pris.")
            else:
                raise ConflictException(detail="Cet email est déjà associé à un compte.")

        # Hasher le mot de passe
        hashed_password = get_password_hash(user.password)

        # Créer l'utilisateur
        new_user = User(
            username=user.username,
            email=user.email,
            password_hash=hashed_password
        )
        self.db.add(new_user)
        await self.db.flush()

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_active": new_user.is_active,
            "role": new_user.role,
            "created_at": new_user.created_at
        }

    async def login_for_access_token(self, form_data: OAuth2PasswordRequestForm, response: Response):
        query = select(User).where(User.username == form_data.username)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.username, "id": user.id, "role": user.role}, expires_delta=access_token_expires
        )

        new_session = UserSession(
            user_id=user.id,
            token=access_token,
            expires_at=datetime.now(timezone.utc) + access_token_expires
        )
        self.db.add(new_session)
        await self.db.flush()

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=True,  # Obligatoire si samesite="none" (fonctionne sur localhost)
            samesite="none",  # Indispensable pour autoriser le cookie entre le port 3000 et 8000
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )

        return {"access_token": access_token, "token_type": "bearer"}
    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        smtp_host = settings.SMTP_HOST
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD

        message = MIMEMultipart()
        message["From"] = smtp_user
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, message.as_string())
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'envoi de l'e-mail : {str(e)}")

    async def request_password_reset(self, email: str):
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=404,
                detail="E-mail non enregistré"
            )

        # Générer un token de réinitialisation aléatoire
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)

        # Sauvegarder le token
        new_token = PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            expires_at=expires_at
        )
        self.db.add(new_token)
        await self.db.flush()

        # Générer l'e-mail contenant le lien de réinitialisation
        reset_link = f"{settings.BACKEND_CORS_ORIGINS}/reset-password-verification/{reset_token}"
        email_subject = "Réinitialisation de votre mot de passe"
        email_body = f"""
        Bonjour,

        Vous avez demandé une réinitialisation de votre mot de passe. Cliquez sur le lien ci-dessous pour le réinitialiser :
        {reset_link}

        Ce lien expirera dans une heure. Si vous n'avez pas demandé cette réinitialisation, veuillez ignorer cet e-mail.

        Cordialement,
        L'équipe de support
        """
        # Envoyer l'e-mail
        AuthService.send_email(email, email_subject, email_body)

        return {
            "detail": "Un e-mail contenant un lien de réinitialisation de mot de passe a été envoyé."
        }

    async def reset_password(self, reset_data: PasswordResetConfirmSchema):
        data_dict = reset_data.model_dump() if isinstance(reset_data, PasswordResetConfirmSchema) else reset_data

        if len(data_dict["new_password"]) < 8:
            raise BadRequestException(detail="Le mot de passe doit contenir au moins 8 caractères")
        token = data_dict["token"]
        new_password = data_dict["new_password"]

        query = select(PasswordResetToken).where(PasswordResetToken.token == token)
        result = await self.db.execute(query)
        reset_entry = result.scalars().first()

        if not reset_entry:
            raise AuthenticationException(detail="Token invalide")

        # Comparer l'heure actuelle en UTC
        if datetime.now(tz=timezone.utc) > reset_entry.expires_at.replace(tzinfo=timezone.utc):
            raise AuthenticationException(detail="Token expiré")

        # Hasher le nouveau mot de passe
        hashed_password = get_password_hash(new_password)

        # Mettre à jour le mot de passe de l'utilisateur
        user = await self.db.get(User, reset_entry.user_id)
        if user:
            user.password_hash = hashed_password

        # Supprimer le token utilisé
        await self.db.delete(reset_entry)
        await self.db.flush()

        return {
            "detail": "Mot de passe réinitialisé avec succès"
        }
