from fastapi import HTTPException
from psycopg2 import sql

from app.db.database import get_db_connection
from app.schemas import CreateData
from app.schemas.categorie import CategorieBase
from app.schemas.categorie import CategoryUpdate


class CategoryService:
    @staticmethod
    def get_all_categories() -> list[CategorieBase]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories")
        categories = cur.fetchall()
        categoryF = []
        for i in categories:
            categoryDict = {
                "id": i[0],
                "nom": i[1],
                "description": i[2],
            }
            categoryF.append(categoryDict)
        conn.close()
        return categoryF

    @staticmethod
    def get_one_category(id_category: int) -> CategorieBase:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories WHERE id = %s", (id_category,))
        category = cur.fetchone()
        categoryDict = {
            "id": category[0],
            "nom": category[1],
            "description": category[2],
        }
        conn.close()
        return categoryDict

    @staticmethod
    def update_category(id_type: int, data: CategoryUpdate):
        conn = get_db_connection()
        cur = conn.cursor()

        # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
        allowed_fields = {"nom", "description", }
        field = data["field"]

        # Vérifiez si le champ est dans la liste autorisée
        if field not in allowed_fields:
            conn.close()
            raise ValueError(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

        try:
            # Construction sécurisée de la requête
            query = sql.SQL(f"UPDATE categories SET {field} = %s WHERE id = %s").format(
                field=sql.Identifier(field)
            )
            # Exécuter la requête avec des paramètres sûrs
            cur.execute(query, (data["value"], id_type))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    @staticmethod
    def add_category(data: CreateData):
        conn = get_db_connection()
        cursor = conn.cursor()
        data = data.model_dump() if isinstance(data, CreateData) else data
        cursor.execute("SELECT id FROM categories WHERE nom = %s;", (data["value"],))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Category already exists")
        cursor.execute("INSERT INTO categories (nom) VALUES  (%s);", (data["value"],))
        conn.commit()
        cursor.close()
        conn.close()
