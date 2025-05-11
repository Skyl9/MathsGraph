from fastapi import HTTPException

from app.db.database import get_db_connection
from app.schemas import CreateSource


class SourceService:
    @staticmethod
    def create_source(data: CreateSource):
        data = data.model_dump() if isinstance(data, CreateSource) else data
        data = data["value"]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sources WHERE titre = %s;", (data["source"],))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Source already exists")
        cursor.execute("INSERT INTO sources (titre,auteur,annee,url,type) VALUES  (%s,%s,%s,%s,%s) RETURNING id;",
                       (data["source"], data["auteur"], data["annee"], data["url"], data["type"]))
        source_id = cursor.fetchone()[0]
        cursor.execute("INSERT INTO concepts_sources (concept_id, source_id) VALUES  (%s,%s);", (data["id"], source_id))
        conn.commit()
        cursor.close()
        conn.close()