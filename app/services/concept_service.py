from app.core.exceptions import NotFoundException
from app.db.database import get_db_connection
import psycopg2.extras



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
