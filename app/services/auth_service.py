import secrets
import smtplib
from datetime import timedelta, datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
            "SELECT id, username,role, password_hash FROM users WHERE username = %s",
            (form_data.username,)
        )
        user = cursor.fetchone()

        if not user or not verify_password(form_data.password, user[3]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Nom d'utilisateur ou mot de passe incorrect",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user[1],"id":user[0],"role":user[2]}, expires_delta=access_token_expires
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


    @staticmethod
    def request_password_reset(email: str):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifier si l'utilisateur existe
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        if not user:
            raise HTTPException(
                status_code=404,
                detail="E-mail non enregistré"
            )

        # Générer un token de réinitialisation aléatoire
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=1)  # Expiration dans 1 heure

        # Sauvegarder le token et sa date d'expiration
        cursor.execute(
            """
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user[0], reset_token, expires_at)
        )
        conn.commit()

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


    @staticmethod
    def reset_password(token: str, new_password: str):
        conn = get_db_connection()
        cursor = conn.cursor()

        # Vérifier si le token est valide
        cursor.execute(
            """
            SELECT user_id, expires_at
            FROM password_reset_tokens
            WHERE token = %s
            """,
            (token,)
        )
        print("hi1")
        reset_entry = cursor.fetchone()
        if not reset_entry:
            raise HTTPException(
                status_code=404,
                detail="Token invalide"
            )

        user_id, expires_at = reset_entry
        print(expires_at)
        print(datetime.now(tz=timezone.utc))

            # Comparer l'heure actuelle en UTC (aware) avec expires_at
        if datetime.now(tz=timezone.utc) > expires_at:
            raise HTTPException(
                status_code=400,
                detail="Token expiré"
            )

        # Hasher le nouveau mot de passe
        hashed_password = get_password_hash(new_password)

        # Mettre à jour le mot de passe de l'utilisateur
        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE id = %s
            """,
            (hashed_password, user_id)
        )

        # Supprimer le token utilisé
        cursor.execute(
            "DELETE FROM password_reset_tokens WHERE token = %s",
            (token,)
        )
        conn.commit()
        print("hi ?")

        return {
            "detail": "Mot de passe réinitialisé avec succès"
        }

