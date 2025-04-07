from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras
from starlette.middleware.cors import CORSMiddleware

from database import get_db_connection

conn = get_db_connection()
curs = conn.cursor()

def obtenir_dictionnaire_concepts(conn):
    """Récupère les informations des concepts et leurs positions."""

    cur = conn.cursor()

    # Récupérer les informations de base des concepts
    cur.execute("SELECT id, nom, type FROM concepts;")
    concepts = cur.fetchall()

    # Récupérer les positions des concepts
    cur.execute("SELECT concept_id, vue, x, y, z FROM positions WHERE vue IN ('grille', 'arbre');")
    positions = cur.fetchall()

    # Créer un dictionnaire de positions par concept_id
    positions_dict = {}
    for concept_id, vue, x, y, z in positions:
        if concept_id not in positions_dict:
            positions_dict[concept_id] = {}
        positions_dict[concept_id][vue] = {"x": x, "y": y, "z": z}

    # Construire le dictionnaire final
    result = []
    for concept_id, nom, concept_type in concepts:
        result.append({
            "id": concept_id,
            "nom": nom,
            "typeMath": concept_type,
            "position": positions_dict.get(concept_id, {})
        })

    return result

a = obtenir_dictionnaire_concepts(conn)
print(a)
conn.close()