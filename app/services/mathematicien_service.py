import logging

from psycopg import AsyncConnection
from psycopg2 import sql

from app.core.exceptions import ForbiddenException, InternalServerError, ConflictException
from app.schemas import CreateData
from app.schemas.mathematicien import MathematicienResponse, MathematicienUpdate

logger = logging.getLogger(__name__)

class MathematicienService:
    def __init__(self, db: AsyncConnection):
        self.db = db

    async def get_all_mathematicien_name(self):
        async with self.db.cursor() as cur:
            await cur.execute("SELECT id,nom FROM mathematiciens")
            mathematiciens = await cur.fetchall()
        mathematicienF = []
        for i in mathematiciens:
            categoryDict = {
                "id": i[0],
                "nom": i[1],
            }
            mathematicienF.append(categoryDict)
        return mathematicienF

    async def get_one_mathematicien(self, id_mathematicien: int) -> MathematicienResponse:
        async with self.db.cursor() as cur:
            await cur.execute("SELECT * FROM mathematiciens WHERE id = %s", (id_mathematicien,))
            mathematiciens = await cur.fetchone()
            mathematiciensDict = {
                "id": mathematiciens[0],
                "nom": mathematiciens[1],
                "date_naissance": mathematiciens[2],
                "date_deces": mathematiciens[3],
                "biographie": mathematiciens[4],
                "nationalite": mathematiciens[5],
                "domaine": mathematiciens[6],
                "url": mathematiciens[7],
                "recompenses": mathematiciens[8],
                "epoque": mathematiciens[9],
            }
        return mathematiciensDict

    async def update_mathematicien(self, id_mathematicien: int, data: MathematicienUpdate):
        data = data.model_dump() if isinstance(data, MathematicienUpdate) else data

        # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
        allowed_fields = {"nom", "date_naissance", "date_deces", "biographie", "nationalite", "domaine", "url",
                          "recompenses", "epoque"}
        field = data["field"]
        if field not in allowed_fields:
            raise ForbiddenException(detail=f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")
        try:
            async with self.db.cursor() as cur:
                # Vérifiez si le champ est dans la liste autorisée
                # Construction sécurisée de la requête
                query = sql.SQL(f"UPDATE mathematiciens SET {field} = %s WHERE id = %s").format(
                    field=sql.Identifier(field)
                )
                # Exécuter la requête avec des paramètres sûrs
                await cur.execute(query, (data["value"], id_mathematicien))


        except Exception as e:
            raise InternalServerError(detail=e)

    async def get_all_mathematicien_info(self):
        async with self.db.cursor() as cur:
            await cur.execute("SELECT * FROM mathematiciens")
            mathematiciens = await cur.fetchall()
        return mathematiciens

    async def add_mathematicien(self, data: CreateData):
        data = data.model_dump() if isinstance(data, CreateData) else data
        async with self.db.cursor() as cur:
            await cur.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
            if await cur.fetchone() is not None:
                raise ConflictException(detail="Type already exists")
            await cur.execute("INSERT INTO mathematiciens (nom) VALUES  (%s);", (data["value"],))

    async def get_mathematicien_id(self, nom):
        async with self.db.cursor() as cursor:
            await cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (nom,))
            mathematicien = await cursor.fetchone()
        if mathematicien is None:
            return None
        return {"id": mathematicien[0], "nom": nom}
