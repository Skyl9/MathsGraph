import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import CreateData
from app.core.exceptions import ForbiddenException, ConflictException, NotFoundException
from app.schemas.mathematicien import MathematicienUpdate
from app.db.models import Mathematicien
from app.repositories.mathematicien_repository import MathematicienRepository

logger = logging.getLogger(__name__)


class MathematicienService:
    def __init__(self, db: AsyncSession):
        self.repo = MathematicienRepository(db)

    async def get_all_mathematicien_name(self):
        rows = await self.repo.get_all_names()
        return [{"id": r.id, "nom": r.nom} for r in rows]

    async def get_one_mathematicien(self, id_mathematicien: int) -> dict:
        math = await self.repo.get_by_id(id_mathematicien)
        if not math:
            raise NotFoundException(f"Mathematicien with ID {id_mathematicien} not found")

        return {
            "id": math.id,
            "nom": math.nom,
            "date_naissance": math.date_naissance,
            "date_deces": math.date_deces,
            "biographie": math.biographie,
            "nationalite": math.nationalite,
            "domaine": math.domaine,
            "url": math.url,
            "recompenses": math.recompenses,
            "epoque": math.epoque,
        }

    async def update_mathematicien(self, mathematicien_id: int, payload: MathematicienUpdate) -> None:
        payload_dict = payload.model_dump() if isinstance(payload, MathematicienUpdate) else payload

        allowed_fields = {
            "nom",
            "date_naissance",
            "date_deces",
            "biographie",
            "nationalite",
            "domaine",
            "url",
            "recompenses",
            "epoque",
        }
        field = payload_dict["field"]
        if field not in allowed_fields:
            raise ForbiddenException(detail=f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        math = await self.repo.get_by_id(mathematicien_id)
        if not math:
            raise NotFoundException(f"Mathematicien with ID {mathematicien_id} not found")

        setattr(math, field, payload_dict["value"])
        await self.repo.flush()

    async def get_all_mathematicien_info(self):
        return await self.repo.get_all_info()

    async def add_mathematicien(self, data: CreateData):
        payload = data.model_dump() if isinstance(data, CreateData) else data
        nom = payload["value"]

        math_id = await self.repo.get_id_by_name(nom)
        if math_id is not None:
            raise ConflictException(detail="Type already exists")

        new_math = Mathematicien(nom=nom)
        await self.repo.add(new_math)

    async def get_mathematicien_id(self, nom: str):
        math_id = await self.repo.get_id_by_name(nom)
        if math_id is None:
            return None
        return {"id": math_id, "nom": nom}

    async def get_timeline_data(self):
        rows = await self.repo.get_timeline_data()

        return [
            {
                "id": r.id,
                "nom": r.nom,
                "date_naissance": r.date_naissance.isoformat() if r.date_naissance else None,
                "date_deces": r.date_deces.isoformat() if r.date_deces else None,
                "biographie": r.biographie[:200] + "..." if r.biographie and len(r.biographie) > 200 else r.biographie,
                "epoque": r.epoque,
            }
            for r in rows
        ]
