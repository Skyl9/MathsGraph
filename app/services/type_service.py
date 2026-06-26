import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Type
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException, BadRequestException
from app.schemas import CreateData
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom
from app.repositories.type_repository import TypeRepository

logger = logging.getLogger(__name__)


class TypeService:
    def __init__(self, db: AsyncSession):
        self.repo = TypeRepository(db)

    async def get_all_type_name(self) -> list[TypeNom]:
        types_fetched = await self.repo.get_all()

        return [TypeNom(id=t.id, nom=t.type) for t in types_fetched]

    async def get_one_type(self, id_type: int) -> TypeResponse:
        type_fetched = await self.repo.get_by_id(id_type)

        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {id_type}")

        return TypeResponse(
            id=type_fetched.id,
            type=type_fetched.type,
        )

    async def update_type(self, id_type: int, data: TypeUpdate, current_user: dict):
        role = current_user.get("role", "").lower() if current_user else ""
        if role not in ["admin", "moderator"]:
            raise ForbiddenException(detail="Vous n'avez pas les droits pour modifier cette ressource.")

        data_dict = data.model_dump() if isinstance(data, TypeUpdate) else data
        allowed_fields = {"type"}
        field: str = data_dict["field"]

        if field not in allowed_fields:
            raise ForbiddenException(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        type_fetched = await self.repo.get_by_id(id_type)
        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {id_type}")

        setattr(type_fetched, field, data_dict["value"])

        await self.repo.flush()

    async def add_type(self, data: CreateData, current_user: dict):
        role = current_user.get("role", "").lower() if current_user else ""
        if role not in ["admin", "moderator"]:
            raise ForbiddenException(detail="Vous n'avez pas les droits pour modifier cette ressource.")

        data_dict = data.model_dump() if isinstance(data, CreateData) else data
        nom_type = data_dict["value"]

        if not nom_type:
            raise BadRequestException(detail="Type vide")

        existing_type = await self.repo.get_by_name(nom_type)
        if existing_type is not None:
            raise ConflictException(detail="Type already exists")

        new_type = Type(type=nom_type)
        await self.repo.add(new_type)

    async def get_type_by_name(self, nom: str):
        type_fetched = await self.repo.get_by_name(nom)

        if not type_fetched:
            raise NotFoundException(f"Type introuvable : {nom}")

        return {"id": type_fetched.id, "type": type_fetched.type}
