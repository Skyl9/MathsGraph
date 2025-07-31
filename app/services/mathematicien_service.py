from fastapi import HTTPException
from psycopg2 import sql

from app.db.database import get_db_connection
from app.schemas import CreateData, UpdateConceptDict
from app.schemas.mathematicien import MathematicienResponse, MathematicienUpdate


class MathematicienService:
    @staticmethod
    def get_all_mathematicien_name():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id,nom FROM mathematiciens")
        mathematiciens = cur.fetchall()
        mathematicienF = []
        for i in mathematiciens:
            categoryDict = {
                "id": i[0],
                "nom": i[1],
            }
            mathematicienF.append(categoryDict)
        conn.close()
        return mathematicienF

    @staticmethod
    def get_one_mathematicien(id_mathematicien: int) -> MathematicienResponse:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mathematiciens WHERE id = %s", (id_mathematicien,))
        mathematiciens = cur.fetchone()
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
        conn.close()
        return mathematiciensDict

    @staticmethod
    def update_mathematicien(id_mathematicien: int, data: MathematicienUpdate):
        conn = get_db_connection()
        cur = conn.cursor()
        data = data.model_dump() if isinstance(data, MathematicienUpdate) else data

        # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
        allowed_fields = {"nom", "date_naissance", "date_deces", "biographie", "nationalite", "domaine", "url",
                          "recompenses", "epoque"}
        field = data["field"]

        # Vérifiez si le champ est dans la liste autorisée
        if field not in allowed_fields:
            conn.close()
            raise ValueError(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        try:
            # Construction sécurisée de la requête
            query = sql.SQL(f"UPDATE mathematiciens SET {field} = %s WHERE id = %s").format(
                field=sql.Identifier(field)
            )
            # Exécuter la requête avec des paramètres sûrs
            cur.execute(query, (data["value"], id_mathematicien))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def get_all_mathematicien_info():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM mathematiciens")
        mathematiciens = cur.fetchall()
        conn.close()
        return mathematiciens

    @staticmethod
    def add_mathematicien(data: CreateData):
        conn = get_db_connection()
        cursor = conn.cursor()
        data = data.model_dump() if isinstance(data, CreateData) else data
        cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Type already exists")
        cursor.execute("INSERT INTO mathematiciens (nom) VALUES  (%s);", (data["value"],))
        conn.commit()
        conn.close()

    @staticmethod
    def get_mathematicien_id(nom):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (nom,))
        mathematicien = cursor.fetchone()
        if mathematicien is None:
            return None
        return {"id":mathematicien[0],"nom":nom}