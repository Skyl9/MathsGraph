import logging
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException
from app.db.models import Comment
from app.repositories.comments_repository import CommentsRepository

logger = logging.getLogger(__name__)


class CommentsService:
    def __init__(self, db: AsyncSession):
        self.repo = CommentsRepository(db)

    async def get_comments(self, concept_id: int) -> list[dict]:
        comments = await self.repo.get_comments_by_concept(concept_id)

        return [
            {
                "id": c.id,
                "concept_id": c.concept_id,
                "user_id": c.user_id,
                "content": c.content,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "parent_id": c.parent_id,
                "is_deleted": c.is_deleted,
                "field": c.field,
                "username": c.user.username if c.user else None,
            }
            for c in comments
        ]

    async def add_comment(
        self,
        concept_id: int,
        field: str,
        username: str | None,
        content: str,
        parent_id: int | None = None,
    ) -> dict:
        if username is None:
            raise NotFoundException(detail="Utilisateur introuvable")

        # Récupérer l'ID utilisateur
        user_id = await self.repo.get_user_id_by_username(username)
        if user_id is None:
            raise NotFoundException(detail="Utilisateur introuvable")

        # Vérifier si le concept existe
        concept = await self.repo.get_concept_by_id(concept_id)
        if not concept:
            raise NotFoundException(detail="Concept introuvable")

        actual_parent_id = None if parent_id == 0 else parent_id

        new_comment = Comment(
            concept_id=concept_id, user_id=user_id, content=content, parent_id=actual_parent_id, field=field
        )
        await self.repo.add_comment(new_comment)

        return {
            "id": new_comment.id,
            "concept_id": new_comment.concept_id,
            "user_id": new_comment.user_id,
            "content": new_comment.content,
            "created_at": new_comment.created_at,
            "updated_at": new_comment.updated_at,
            "parent_id": new_comment.parent_id,
            "is_deleted": new_comment.is_deleted,
            "field": new_comment.field,
        }

    async def update_comment(self, comment_id: int, content: str, current_user: dict) -> dict:
        comment = await self.repo.get_comment_by_id(comment_id)

        if not comment or comment.is_deleted:
            raise NotFoundException(detail="Commentaire introuvable ou supprimé")

        comment_user_id = int(comment.user_id) if comment.user_id else 0
        token_user_id = int(current_user.get("id", 0))

        is_author = token_user_id == comment_user_id
        is_admin = current_user.get("role") in ["admin", "moderator"]

        if not (is_author or is_admin):
            raise ForbiddenException(detail="Vous n'êtes pas autorisé à modifier ce commentaire.")

        comment.content = content
        # updated_at est géré par server_default=func.now() ou onupdate=func.now() dans les modèles si configuré,
        # sinon on peut le faire manuellement ici si nécessaire.
        # Dans models.py: created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
        # updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
        # Il manque onupdate sur updated_at dans models.py, mais gardons la logique du service original:
        comment.updated_at = func.now()

        await self.repo.flush()
        await self.repo.refresh(comment)

        return {
            "id": comment.id,
            "concept_id": comment.concept_id,
            "user_id": comment.user_id,
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "parent_id": comment.parent_id,
            "is_deleted": comment.is_deleted,
            "field": comment.field,
        }

    async def delete_comment(self, comment_id: int, current_user: dict) -> None:
        comment = await self.repo.get_comment_by_id(comment_id)

        if not comment:
            raise NotFoundException("Commentaire introuvable")
        if comment.is_deleted:
            raise NotFoundException("Commentaire déjà supprimé")

        comment_user_id = int(comment.user_id) if comment.user_id else 0
        token_user_id = int(current_user.get("id", 0))

        is_author = token_user_id == comment_user_id
        is_admin = current_user.get("role") in ["admin", "moderator"]

        if not (is_author or is_admin):
            raise ForbiddenException("Vous n'êtes pas autorisé à supprimer ce commentaire.")

        comment.is_deleted = True
        await self.repo.flush()

    async def get_recent_comments(self, limit: int = 20) -> list[dict]:
        comments = await self.repo.get_recent_comments(limit)

        return [
            {
                "id": c.id,
                "concept_id": c.concept_id,
                "concept_nom": c.concept.nom if c.concept else None,
                "user_id": c.user_id,
                "username": c.user.username if c.user else None,
                "content": c.content,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "field": c.field,
            }
            for c in comments
        ]
