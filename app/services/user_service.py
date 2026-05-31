from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException, BadRequestException, InternalServerError, ForbiddenException
from app.schemas.user import UserId, UpdateUser, Favorite
from app.db.models import User, UserFavorite, Concept, Mathematicien, Category, Type, ConceptVersion

import logging

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, id_user: int):
        query = select(User).where(User.id == id_user)
        result = await self.db.execute(query)
        user = result.scalars().first()

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
        query = select(User.id).where(User.username == username)
        result = await self.db.execute(query)
        user_id = result.scalars().first()
        if user_id is None:
            raise NotFoundException(detail="User not found")
        return UserId(id=user_id)

    async def patch_user(self, id: int, data: UpdateUser, current_user: dict) -> None:
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

        query = select(User).where(User.id == id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user:
            raise NotFoundException(detail="User not found")

        setattr(user, field, data_dict["value"])
        await self.db.flush()

    async def get_favorite_user(self, user_id: int):
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalars().first()

        if not user:
            raise NotFoundException(detail="User not found")

        query_fav = (
            select(UserFavorite)
            .where(UserFavorite.user_id == user_id)
            .options(
                selectinload(UserFavorite.concept),
                selectinload(UserFavorite.mathematicien),
                selectinload(UserFavorite.category),
                selectinload(UserFavorite.type),
            )
        )
        result_fav = await self.db.execute(query_fav)
        favorites = result_fav.scalars().all()

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

    async def delete_favorite_user(self, general_id: int, data: Favorite) -> None:
        data_dict = data.model_dump() if isinstance(data, Favorite) else data
        user_id = int(data_dict["user_id"])
        entity_type = data_dict["type"]

        query_user = select(User.id).where(User.id == user_id)
        res_user = await self.db.execute(query_user)
        if not res_user.scalars().first():
            raise NotFoundException(detail="User not found")

        # Vérifier l'existence de l'entité correcte selon son type
        if entity_type == "concept":
            res = await self.db.execute(select(Concept.id).where(Concept.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Concept not found")
        elif entity_type == "mathematicien":
            res = await self.db.execute(select(Mathematicien.id).where(Mathematicien.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Mathématicien not found")
        elif entity_type == "category":
            res = await self.db.execute(select(Category.id).where(Category.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Catégorie not found")
        elif entity_type == "type":
            res = await self.db.execute(select(Type.id).where(Type.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Type not found")
        else:
            raise BadRequestException(detail=f"Type de favori inconnu : {entity_type}")

        stmt = delete(UserFavorite).where(UserFavorite.user_id == user_id)
        if entity_type == "concept":
            stmt = stmt.where(UserFavorite.concept_id == general_id)
        elif entity_type == "mathematicien":
            stmt = stmt.where(UserFavorite.mathematicien_id == general_id)
        elif entity_type == "category":
            stmt = stmt.where(UserFavorite.category_id == general_id)
        elif entity_type == "type":
            stmt = stmt.where(UserFavorite.type_id == general_id)

        await self.db.execute(stmt)
        await self.db.flush()

    async def add_favorite_user(self, general_id: int, data: Favorite) -> None:
        data_dict = data.model_dump() if isinstance(data, Favorite) else data
        user_id = int(data_dict["user_id"])
        entity_type = data_dict["type"]

        query_user = select(User.id).where(User.id == user_id)
        res_user = await self.db.execute(query_user)
        if not res_user.scalars().first():
            raise NotFoundException(detail="User not found")

        # Vérifier l'existence de l'entité correcte selon son type
        if entity_type == "concept":
            res = await self.db.execute(select(Concept.id).where(Concept.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Concept not found")
        elif entity_type == "mathematicien":
            res = await self.db.execute(select(Mathematicien.id).where(Mathematicien.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Mathématicien not found")
        elif entity_type == "category":
            res = await self.db.execute(select(Category.id).where(Category.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Catégorie not found")
        elif entity_type == "type":
            res = await self.db.execute(select(Type.id).where(Type.id == general_id))
            if not res.scalars().first():
                raise NotFoundException(detail="Type not found")
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

        self.db.add(new_fav)
        await self.db.flush()

    async def get_history_user(self, user_id: int, limit: int = 20) -> list[dict]:
        query_user = select(User.id).where(User.id == user_id)
        res_user = await self.db.execute(query_user)
        if not res_user.scalars().first():
            raise NotFoundException(detail="User not found")

        query = (
            select(ConceptVersion)
            .where(ConceptVersion.modified_by == user_id)
            .options(selectinload(ConceptVersion.concept), selectinload(ConceptVersion.modifier))
            .order_by(ConceptVersion.modified_at.desc())
            .limit(limit)
        )

        try:
            result = await self.db.execute(query)
            versions = result.scalars().all()

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
