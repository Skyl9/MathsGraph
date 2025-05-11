from fastapi import HTTPException

from app.db.database import get_db_connection
from app.schemas import CreateRelation


class RelationService:
    @staticmethod
    def add_relation(data: CreateRelation):
        data = data.model_dump() if isinstance(data, CreateRelation) else data
        data = data["value"]
        conn = get_db_connection()
        cursor = conn.cursor()
        print(data["théo1"].strip(), data["théo2"])
        cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo1"],))
        theo1 = cursor.fetchone()
        cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo2"],))
        theo2 = cursor.fetchone()
        cursor.execute("SELECT id FROM relations WHERE concept_source = %s AND concept_cible = %s;", (theo1, theo2))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Relation already exists")
        if theo1 is None or theo2 is None:
            print(theo1, theo2)
            raise HTTPException(status_code=404, detail="Concept not found")
        cursor.execute(
            "INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES  (%s,%s,%s,%s);",
            (theo1[0], theo2[0], data["relation"], data["desc"]))
        conn.commit()
        cursor.close()
        conn.close()