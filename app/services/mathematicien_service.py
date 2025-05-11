from psycopg2 import sql

from app.db.database import get_db_connection
from app.schemas.mathematicien import MathematicienResponse, MathematicienUpdate


def get_all_mathematicien_info():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM mathematiciens")
    mathematiciens = cur.fetchall()
    conn.close()
    return mathematiciens

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

def get_one_mathematicien(id_mathematicien:int)->MathematicienResponse:
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
        "domaine" : mathematiciens[6],
        "url":mathematiciens[7],
        "recompenses":mathematiciens[8],
        "epoque":mathematiciens[9],

    }
    conn.close()
    return mathematiciensDict

def update_mathematicien(id_mathematicien: int, data: MathematicienUpdate):
    conn = get_db_connection()
    cur = conn.cursor()

    # Liste des colonnes autorisées pour éviter les problèmes d'injection SQL
    allowed_fields = {"nom", "date_naissance", "date_deces", "biographie", "nationalite", "domaine", "url", "recompenses", "epoque"}
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
