import logging
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenException, InternalServerError, ConflictException, NotFoundException
from app.schemas import CreateData
from app.schemas.mathematicien import MathematicienResponse, MathematicienUpdate
from app.db.models import Mathematicien

logger = logging.getLogger(__name__)

class MathematicienService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all_mathematicien_name(self):
        query = select(Mathematicien.id, Mathematicien.nom)
        result = await self.db.execute(query)
        rows = result.all()
        return [{"id": r.id, "nom": r.nom} for r in rows]

    async def get_one_mathematicien(self, id_mathematicien: int) -> dict:
        math = await self.db.get(Mathematicien, id_mathematicien)
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

    async def update_mathematicien(self, id_mathematicien: int, data: MathematicienUpdate):
        data_dict = data.model_dump() if isinstance(data, MathematicienUpdate) else data

        allowed_fields = {"nom", "date_naissance", "date_deces", "biographie", "nationalite", "domaine", "url",
                          "recompenses", "epoque"}
        field = data_dict["field"]
        if field not in allowed_fields:
            raise ForbiddenException(detail=f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        math = await self.db.get(Mathematicien, id_mathematicien)
        if not math:
            raise NotFoundException(f"Mathematicien with ID {id_mathematicien} not found")

        setattr(math, field, data_dict["value"])
        await self.db.flush()

    async def get_all_mathematicien_info(self):
        query = select(Mathematicien)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def add_mathematicien(self, data: CreateData):
        payload = data.model_dump() if isinstance(data, CreateData) else data
        nom = payload["value"]
        
        query = select(Mathematicien.id).where(Mathematicien.nom == nom)
        result = await self.db.execute(query)
        if result.scalars().first() is not None:
            raise ConflictException(detail="Type already exists")
            
        new_math = Mathematicien(nom=nom)
        self.db.add(new_math)
        await self.db.flush()

    async def get_mathematicien_id(self, nom: str):
        query = select(Mathematicien.id).where(Mathematicien.nom == nom)
        result = await self.db.execute(query)
        math_id = result.scalar_one_or_none()
        if math_id is None:
            return None
        return {"id": math_id, "nom": nom}

    async def get_timeline_data(self):
        query = (
            select(Mathematicien)
            .where(Mathematicien.date_naissance.isnot(None))
            .order_by(Mathematicien.date_naissance.asc())
        )
        result = await self.db.execute(query)
        rows = result.scalars().all()

        return [
            {
                "id": r.id,
                "nom": r.nom,
                "date_naissance": r.date_naissance.isoformat() if r.date_naissance else None,
                "date_deces": r.date_deces.isoformat() if r.date_deces else None,
                "biographie": r.biographie[:200] + "..." if r.biographie and len(r.biographie) > 200 else r.biographie,
                "epoque": r.epoque
            } for r in rows
        ]
