from psycopg2 import sql

from app.db.database import get_db_connection
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom


def get_all_type_name()->list[TypeNom]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, type FROM type")
    typeFetched = cur.fetchall()
    print(typeFetched)
    typeF = []
    for i in typeFetched:
        categoryDict = {
            "id": i[0],
            "type": i[1],
        }
        typeF.append(categoryDict)
    return typeF
def get_one_type(id_type: int) -> TypeResponse:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM type WHERE id = %s", (id_type,))
    concept_type = cur.fetchone()
    typeDict = {
        "id": concept_type[0],
        "type": concept_type[1],
    }
    conn.close()
    return typeDict


def update_type(id_type: int, data: TypeUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
    allowed_fields = {"type"}
    field = data["field"]

    # Vérifiez si le champ est dans la liste autorisée
    if field not in allowed_fields:
        conn.close()
        raise ValueError(f"Le champ '{field}' n'est pas autorisé pour une mise à jour.")

    try:
        # Construction sécurisée de la requête
        query = sql.SQL(f"UPDATE type SET {field} = %s WHERE id = %s").format(
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
