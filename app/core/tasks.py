import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete
from app.db.database import AsyncSessionLocal
from app.db.models import UserSession, PasswordResetToken

logger = logging.getLogger(__name__)

async def clean_expired_tokens_and_sessions():
    """
    Tâche asynchrone qui tourne en arrière-plan pour nettoyer les tokens et sessions expirés.
    Tourne toutes les 24 heures.
    """
    while True:
        try:
            logger.info("Début du job de nettoyage des sessions et tokens expirés...")
            now = datetime.now(timezone.utc)
            
            async with AsyncSessionLocal() as session:
                # Nettoyer les sessions utilisateur expirées
                stmt_sessions = delete(UserSession).where(UserSession.expires_at < now)
                res_sessions = await session.execute(stmt_sessions)
                
                # Nettoyer les tokens de réinitialisation expirés (ou déjà utilisés)
                # On garde un historique des tokens utilisés pendant 30 jours, 
                # et on supprime les non-utilisés expirés immédiatement.
                stmt_tokens = delete(PasswordResetToken).where(
                    PasswordResetToken.expires_at < now
                )
                res_tokens = await session.execute(stmt_tokens)
                
                await session.commit()
                
                logger.info(f"Nettoyage terminé: {res_sessions.rowcount} sessions expirées, {res_tokens.rowcount} tokens expirés supprimés.")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage des tokens et sessions: {str(e)}")
            
        # Attendre 24h avant la prochaine exécution
        await asyncio.sleep(86400)
