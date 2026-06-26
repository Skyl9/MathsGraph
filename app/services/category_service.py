import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.schemas import CreateData
from app.schemas.categorie import CategorieBase, CategoryUpdate
from app.db.models import Category
from app.repositories.category_repository import CategoryRepository
from app.core.security import verify_admin_moderator
from app.core.redis_client import redis_db

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.repo = CategoryRepository(db)

    async def get_all_categories(self) -> list[CategorieBase]:
        categories = await self.repo.get_all()

        return [
            CategorieBase(
                id=c.id,
                nom=c.nom,
                description=c.description,
                parent_id=c.parent_id,
            )
            for c in categories
        ]

    async def get_one_category(self, id_category: int) -> CategorieBase:
        category = await self.repo.get_by_id(id_category)
        if not category:
            raise NotFoundException(detail=f"Category {id_category} not found")

        return CategorieBase(
            id=category.id,
            nom=category.nom,
            description=category.description,
            parent_id=category.parent_id,
        )

    async def update_category(self, id_category: int, data: CategoryUpdate, current_user: dict) -> None:
        verify_admin_moderator(current_user)

        allowed_fields = {"nom", "description", "parent_id"}
        data_dict = data.model_dump() if isinstance(data, CategoryUpdate) else data
        field = data_dict["field"]
        if field not in allowed_fields:
            raise ForbiddenException(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        category = await self.repo.get_by_id(id_category)
        if not category:
            raise NotFoundException(detail=f"Category {id_category} not found")

        setattr(category, field, data_dict["value"])
        await self.repo.flush()

        try:
            await redis_db.delete("mathgraph:data")
        except Exception as e:
            logger.warning(f"Erreur d'invalidation cache Redis: {e}")

    async def add_category(self, data: CreateData, current_user: dict) -> None:
        verify_admin_moderator(current_user)

        payload = data.model_dump() if isinstance(data, CreateData) else data
        nom = payload["value"]

        existing_category = await self.repo.get_by_name(nom)
        if existing_category is not None:
            raise ConflictException(detail=f"Category {nom} already exists")

        new_category = Category(nom=nom)
        await self.repo.add(new_category)

        try:
            await redis_db.delete("mathgraph:data")
        except Exception as e:
            logger.warning(f"Erreur d'invalidation cache Redis: {e}")

    async def get_category_id_by_name(self, name: str):
        category = await self.repo.get_by_name(name)

        if category is None:
            return None
        return {"id": category.id, "nom": name}
