from psycopg2 import sql
from unicodedata import category

from app.db.database import get_db_connection
from app.schemas.categorie import CategoryUpdate
from app.schemas.categorie import CategorieBase

def get_all_categories()->list[CategorieBase]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories")
    categories = cur.fetchall()
    categoryF = []
    for i in categories:
        categoryDict ={
            "id":i[0],
            "nom":i[1],
            "description":i[2],
        }
        categoryF.append(categoryDict)
    conn.close()
    return categoryF

def get_one_category(id_category: int) -> CategorieBase:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id = %s", (id_category,))
    category = cur.fetchone()
    categoryDict = {
        "id": category[0],
        "nom": category[1],
        "description":category[2],
    }
    conn.close()
    return categoryDict


def update_category(id_type: int, data: CategoryUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
    allowed_fields = {"nom","description",}
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
