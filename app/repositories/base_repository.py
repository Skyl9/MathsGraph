from typing import TypeVar, Generic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

T = TypeVar("T")


class BaseRepository(Generic[T]):
    def __init__(self, model: type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get_by_id(self, id: int) -> T | None:
        return await self.db.get(self.model, id)

    async def get_all(self) -> list[T]:
        query = select(self.model)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def add(self, entity: T) -> T:
        self.db.add(entity)
        await self.db.flush()
        return entity

    async def flush(self) -> None:
        await self.db.flush()
