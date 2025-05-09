from psycopg2 import sql

from app.db.database import get_db_connection
from app.schemas.categorie import CategoryUpdate
from app.schemas.categorie import CategorieBase


def get_one_category(id_type: int) -> CategorieBase:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id = %s", (id_type,))
    concept_type = cur.fetchone()
    typeDict = {
        "id": concept_type[0],
        "nom": concept_type[1],
        "description":concept_type[2],
    }
    conn.close()
    return typeDict


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
