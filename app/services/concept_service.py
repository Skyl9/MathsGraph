from app.core.exceptions import NotFoundException
from app.db.database import get_db_connection
import psycopg2.extras

from app.schemas.concept import ConceptName

"""
class ConceptService:
    @staticmethod
    def get_all_concepts():
        conn = get_db_connection()
        try:
            concepts = get_concepts()
            return {'nodes': concepts, "edges": []}
        finally:
            conn.close()

    @staticmethod
    def get_concept_by_id(concept_id: int):
        conn = get_db_connection()
        try:
            concept = get_concept_info(concept_id, conn)
            if not concept:
                raise NotFoundException(f"Concept {concept_id} non trouvé")
            return concept
        finally:
            conn.close()

    @staticmethod
    def update_concept(concept_id: int, data: dict):
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Reprendre la logique de updateOneCategory ici
            # [Code existant de updateOneCategory]
            pass
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=400, detail=str(e))
        finally:
            cursor.close()
            conn.close()
"""


def get_all_concepts_name()->list[ConceptName]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id,nom FROM concepts")

    concepts = cur.fetchall()
    conceptList =[]
    for i in concepts:
        categoryDict = {
            "id":i[0],
            "nom":i[1],
        }
        conceptList.append(categoryDict)
    return conceptList