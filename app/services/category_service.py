import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.schemas import CreateData
from app.schemas.categorie import CategorieBase, CategoryUpdate
from app.db.models import Category

logger = logging.getLogger(__name__)


class CategoryService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_categories(self) -> list[CategorieBase]:
        query = select(Category)
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return [
            {
                "id": c.id,
                "nom": c.nom,
                "description": c.description,
                "parent_id": c.parent_id,
            }
            for c in categories
        ]

    async def get_one_category(self, id_category: int) -> CategorieBase:
        category = await self.db.get(Category, id_category)
        if not category:
            raise NotFoundException(detail=f"Category {id_category} not found")

        return {
            "id": category.id,
            "nom": category.nom,
            "description": category.description,
            "parent_id": category.parent_id,
        }

    async def update_category(self, id_category: int, data: CategoryUpdate) -> None:
        allowed_fields = {"nom", "description", "parent_id"}
        data_dict = data.model_dump() if isinstance(data, CategoryUpdate) else data
        field = data_dict["field"]
        if field not in allowed_fields:
            raise ForbiddenException(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        category = await self.db.get(Category, id_category)
        if not category:
            raise NotFoundException(detail=f"Category {id_category} not found")

        setattr(category, field, data_dict["value"])
        await self.db.flush()

    async def add_category(self, data: CreateData) -> None:
        payload = data.model_dump() if isinstance(data, CreateData) else data
        nom = payload["value"]
        
        query = select(Category).where(Category.nom == nom)
        result = await self.db.execute(query)
        if result.scalars().first() is not None:
            raise ConflictException(detail=f"Category {nom} already exists")

        new_category = Category(nom=nom)
        self.db.add(new_category)
        await self.db.flush()

    async def get_category_id_by_name(self, name: str):
        query = select(Category).where(Category.nom == name)
        result = await self.db.execute(query)
        category = result.scalars().first()

        if category is None:
            return None
        return {"id": category.id, "nom": name}
