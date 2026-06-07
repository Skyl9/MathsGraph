from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from app.db.models import User, UserFavorite, Concept, Mathematicien, Category, Type, ConceptVersion


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_id(self, id_user: int):
        return await self.db.get(User, id_user)

    async def get_id_by_username(self, username: str):
        query = select(User.id).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def check_user_exists(self, id_user: int):
        query = select(User.id).where(User.id == id_user)
        result = await self.db.execute(query)
        return result.scalars().first() is not None

    async def get_favorite_user(self, user_id: int):
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
        return result_fav.scalars().all()

    async def check_entity_exists(self, entity_type: str, entity_id: int):
        model: type[Concept] | type[Mathematicien] | type[Category] | type[Type]
        if entity_type == "concept":
            model = Concept
        elif entity_type == "mathematicien":
            model = Mathematicien
        elif entity_type == "category":
            model = Category
        elif entity_type == "type":
            model = Type
        else:
            return False

        res = await self.db.execute(select(model.id).where(model.id == entity_id))
        return res.scalars().first() is not None

    async def delete_favorite_user(self, user_id: int, entity_type: str, general_id: int):
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
        await self.db.commit()

    async def add_favorite_user(self, fav: UserFavorite):
        self.db.add(fav)
        await self.db.commit()

    async def get_history_user(self, user_id: int, limit: int):
        query = (
            select(ConceptVersion)
            .where(ConceptVersion.modified_by == user_id)
            .options(selectinload(ConceptVersion.concept), selectinload(ConceptVersion.modifier))
            .order_by(ConceptVersion.modified_at.desc())
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def commit(self):
        await self.db.commit()
