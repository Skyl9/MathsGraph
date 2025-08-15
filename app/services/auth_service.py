import secrets
import smtplib
from datetime import timedelta, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from app import settings
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.exceptions import BadRequestException, AuthenticationException
from app.schemas.auth import PasswordResetConfirmSchema, UserCreate
import logging

logger = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def register_user(self, user: UserCreate):
        async with self.db.cursor() as cursor:
            print(f"Connexion utilisée par le service : {self.db.info.backend_pid}")
            print(f"Etat de la transaction avant l'insertion : {self.db.info.transaction_status}")

            # Vérifier si l'utilisateur existe déjà
            await cursor.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                                 (user.username, user.email))
            if await cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail="Username ou email déjà utilisé"
                )

            # Hasher le mot de passe
            hashed_password = get_password_hash(user.password)

            # Créer l'utilisateur
            await cursor.execute(
                """
                INSERT INTO users (username, email, password_hash)
                VALUES (%s, %s, %s)
                RETURNING id, username, email, is_active,role,created_at
                """,
                (user.username, user.email, hashed_password)
            )
            new_user = await cursor.fetchone()
        print(f"Etat de la transaction après l'insertion : {self.db.info.transaction_status}")

        return {
            "id": new_user[0],
            "username": new_user[1],
            "email": new_user[2],
            "is_active": new_user[3],
            "role": new_user[4],
            "created_at": new_user[5]
        }

    async def login_for_access_token(self, form_data: OAuth2PasswordRequestForm = Depends()):

        async with self.db.cursor() as cursor:
            await cursor.execute(
                "SELECT id, username,role, password_hash FROM users WHERE username = %s",
                (form_data.username,)
            )
            user = await cursor.fetchone()
        if not user or not verify_password(form_data.password, user[3]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[1], "id": user[0], "role": user[2]}, expires_delta=access_token_expires
        )

        return {"access_token": access_token, "token_type": "bearer"}

    @staticmethod
    def send_email(to_email: str, subject: str, body: str):
        """
        Envoie un e-mail via un serveur SMTP.
        Args:
            to_email: Adresse e-mail du destinataire.
            subject: Sujet de l'e-mail.
            body: Contenu de l'e-mail.
        """
        smtp_host = settings.SMTP_HOST  # Exemple : "smtp.gmail.com"
        smtp_port = settings.SMTP_PORT  # Exemple : 587
        smtp_user = settings.SMTP_USER  # Adresse email utilisée
        smtp_password = settings.SMTP_PASSWORD  # Mot de passe/liens sécurité (OAuth/token)

        # Création du message e-mail
        message = MIMEMultipart()
        message["From"] = smtp_user
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        try:
            # Connexion au serveur SMTP et envoi
            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.ehlo()
                server.starttls()  # Sécuriser la connexion avec TLS
                server.ehlo()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, to_email, message.as_string())
        except Exception as e:
            raise RuntimeError(f"Erreur lors de l'envoi de l'e-mail : {str(e)}")

    async def request_password_reset(self, email: str):
        async with self.db.cursor() as cursor:
            # Vérifier si l'utilisateur existe
            await cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = await cursor.fetchone()
            if not user:
                raise HTTPException(
                    status_code=404,
                    detail="E-mail non enregistré"
                )

            # Générer un token de réinitialisation aléatoire
            reset_token = secrets.token_urlsafe(32)
            expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)  # Expiration dans 1 heure

            # Sauvegarder le token et sa date d'expiration
            await cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, token, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user[0], reset_token, expires_at)
            )

        # Générer l'e-mail contenant le lien de réinitialisation
        reset_link = f"{settings.RESET_URL}/reset-password-verification/{reset_token}"
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

        reset_data = reset_data.model_dump() if isinstance(reset_data, PasswordResetConfirmSchema) else reset_data

        if len(reset_data["new_password"]) < 8:
            raise BadRequestException(detail="Le mot de passe doit contenir au moins 8 caractères")
        token = reset_data["token"]
        new_password = reset_data["new_password"]

        async with self.db.cursor() as cursor:

            # Vérifier si le token est valide
            await cursor.execute(
                """
                SELECT user_id, expires_at
                FROM password_reset_tokens
                WHERE token = %s
                """,
                (token,)
            )

            reset_entry = await cursor.fetchone()

            if not reset_entry:
                raise AuthenticationException(detail="Token invalide")

            user_id, expires_at = reset_entry

            # Comparer l'heure actuelle en UTC (aware) avec expires_at
            if datetime.now(tz=timezone.utc) > expires_at:
                raise AuthenticationException(detail="Token expiré")

            # Hasher le nouveau mot de passe
            hashed_password = get_password_hash(new_password)

            # Mettre à jour le mot de passe de l'utilisateur
            await cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE id = %s
                """,
                (hashed_password, user_id)
            )

            # Supprimer le token utilisé
            await cursor.execute(
                "DELETE FROM password_reset_tokens WHERE token = %s",
                (token,)
            )
        return {
            "detail": "Mot de passe réinitialisé avec succès"
        }
