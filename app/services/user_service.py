from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, BadRequestException, InternalServerError, ForbiddenException
from app.schemas.user import UserId, UpdateUser, Favorite
from app.db.models import UserFavorite
from app.repositories.user_repository import UserRepository

import logging
from uuid import UUID as PyUUID

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_user_by_id(self, id_user: PyUUID):
        user = await self.repo.get_user_by_id(id_user)

        if user is None:
            raise NotFoundException(detail="User not found")

        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "role": user.role,
            "preferred_language": user.preferred_language,
            "avatar_url": user.avatar_url,
            "bio": user.bio,
        }

    async def get_id_by_username(self, username: str) -> UserId:
        user_id = await self.repo.get_id_by_username(username)
        if user_id is None:
            raise NotFoundException(detail="User not found")
        return UserId(id=user_id)

    async def patch_user(self, id: PyUUID, data: UpdateUser, current_user: dict) -> None:
        """Met à jour un champ utilisateur. Un utilisateur ne peut modifier que son propre profil.
        Les admins peuvent modifier n'importe quel profil."""
        data_dict = data.model_dump() if isinstance(data, UpdateUser) else data
        allowed_fields = {"username", "email", "preferred_language", "avatar_url", "bio"}
        # Les admins peuvent aussi modifier is_active et role
        admin_only_fields = {"is_active", "role"}

        field: str = data_dict["field"]
        caller_role = current_user.get("role", "").lower()
        caller_id = current_user.get("id")

        # Vérification d'autorisation : seul l'utilisateur lui-même ou un admin peut modifier
        if caller_id != id and caller_role != "admin":
            raise ForbiddenException(detail="Vous ne pouvez modifier que votre propre profil.")

        # Les champs sensibles (rôle, is_active) sont réservés aux admins
        if field in admin_only_fields and caller_role != "admin":
            raise ForbiddenException(detail="Seul un administrateur peut modifier ce champ.")

        if field not in allowed_fields and field not in admin_only_fields:
            raise BadRequestException(detail="Mauvais champ donné")

        user = await self.repo.get_user_by_id(id)

        if not user:
            raise NotFoundException(detail="User not found")

        setattr(user, field, data_dict["value"])
        await self.repo.commit()

    async def get_favorite_user(self, user_id: PyUUID):
        exists = await self.repo.check_user_exists(user_id)

        if not exists:
            raise NotFoundException(detail="User not found")

        favorites = await self.repo.get_favorite_user(user_id)

        dictList = []
        for fav in favorites:
            if fav.concept:
                dictList.append({"id": fav.concept.id, "nom": fav.concept.nom, "category": "concept"})
            elif fav.mathematicien:
                dictList.append({"id": fav.mathematicien.id, "nom": fav.mathematicien.nom, "category": "mathematicien"})
            elif fav.category:
                dictList.append({"id": fav.category.id, "nom": fav.category.nom, "category": "category"})
            elif fav.type:
                dictList.append({"id": fav.type.id, "nom": fav.type.type, "category": "type"})
        return dictList

    async def delete_favorite_user(self, general_id: int, data: Favorite, current_user: dict) -> None:
        data_dict = data.model_dump() if isinstance(data, Favorite) else data
        user_id = data_dict["user_id"]

        caller_id = current_user.get("id")
        caller_role = current_user.get("role", "").lower()
        if user_id != caller_id and caller_role != "admin":
            raise ForbiddenException(detail="Not authorized to modify this user's favorites")

        entity_type = data_dict["type"]

        exists = await self.repo.check_user_exists(user_id)
        if not exists:
            raise NotFoundException(detail="User not found")

        # Vérifier l'existence de l'entité correcte selon son type
        entity_exists = await self.repo.check_entity_exists(entity_type, general_id)
        if not entity_exists:
            if entity_type in ["concept", "mathematicien", "category", "type"]:
                raise NotFoundException(detail=f"{entity_type.capitalize()} not found")
            else:
                raise BadRequestException(detail=f"Type de favori inconnu : {entity_type}")

        await self.repo.delete_favorite_user(user_id, entity_type, general_id)

    async def add_favorite_user(self, general_id: int, data: Favorite, current_user: dict) -> None:
        data_dict = data.model_dump() if isinstance(data, Favorite) else data
        user_id = data_dict["user_id"]

        caller_id = current_user.get("id")
        caller_role = current_user.get("role", "").lower()
        if user_id != caller_id and caller_role != "admin":
            raise ForbiddenException(detail="Not authorized to modify this user's favorites")

        entity_type = data_dict["type"]

        exists = await self.repo.check_user_exists(user_id)
        if not exists:
            raise NotFoundException(detail="User not found")

        # Vérifier l'existence de l'entité correcte selon son type
        entity_exists = await self.repo.check_entity_exists(entity_type, general_id)
        if not entity_exists:
            if entity_type in ["concept", "mathematicien", "category", "type"]:
                raise NotFoundException(detail=f"{entity_type.capitalize()} not found")
            else:
                raise BadRequestException(detail=f"Type de favori inconnu : {entity_type}")

        new_fav = UserFavorite(user_id=user_id)
        if entity_type == "concept":
            new_fav.concept_id = general_id
        elif entity_type == "mathematicien":
            new_fav.mathematicien_id = general_id
        elif entity_type == "category":
            new_fav.category_id = general_id
        elif entity_type == "type":
            new_fav.type_id = general_id

        await self.repo.add_favorite_user(new_fav)

    async def get_history_user(self, user_id: PyUUID, limit: int = 20) -> list[dict]:
        exists = await self.repo.check_user_exists(user_id)
        if not exists:
            raise NotFoundException(detail="User not found")

        try:
            versions = await self.repo.get_history_user(user_id, limit)

            contributions = []
            for v in versions:
                contributions.append(
                    {
                        "id": v.id,
                        "concept_id": v.concept_id,
                        "concept_nom": v.concept.nom if v.concept else None,
                        "username": v.modifier.username if v.modifier else None,
                        "modified_at": v.modified_at.isoformat() if v.modified_at else None,
                        "field_modified": v.field_modified,
                        "is_rollback": v.is_rollback,
                    }
                )

            return contributions

        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique de l'utilisateur {user_id} : {e}")
            raise InternalServerError("Impossible de récupérer l'historique de l'utilisateur.")
