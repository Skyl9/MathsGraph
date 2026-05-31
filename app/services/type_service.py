import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Type
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException, BadRequestException
from app.schemas import CreateData
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom

logger = logging.getLogger(__name__)


class TypeService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_type_name(self) -> list[TypeNom]:
        query = select(Type)
        result = await self.db.execute(query)
        types_fetched = result.scalars().all()

        return [TypeNom(id=t.id, nom=t.type) for t in types_fetched]

    async def get_one_type(self, id_type: int) -> TypeResponse:
        type_fetched = await self.db.get(Type, id_type)

        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {id_type}")

        return TypeResponse(
            id=type_fetched.id,
            type=type_fetched.type,
        )

    async def update_type(self, id_type: int, data: TypeUpdate):
        data_dict = data.model_dump() if isinstance(data, TypeUpdate) else data
        allowed_fields = {"type"}
        field: str = data_dict["field"]

        if field not in allowed_fields:
            raise ForbiddenException(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        type_fetched = await self.db.get(Type, id_type)
        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {id_type}")

        setattr(type_fetched, field, data_dict["value"])

        await self.db.flush()

    async def add_type(self, data: CreateData):
        data_dict = data.model_dump() if isinstance(data, CreateData) else data
        nom_type = data_dict["value"]

        if not nom_type:
            raise BadRequestException(detail="Type vide")

        query = select(Type).where(Type.type == nom_type)
        result = await self.db.execute(query)
        if result.scalars().first() is not None:
            raise ConflictException(detail="Type already exists")

        new_type = Type(type=nom_type)
        self.db.add(new_type)
        await self.db.flush()

    async def get_type_by_name(self, nom: str):
        query = select(Type).where(Type.type == nom)
        result = await self.db.execute(query)
        type_fetched = result.scalars().first()

        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {nom}")

        return {"id": type_fetched.id, "type": type_fetched.type}
