from fastapi import HTTPException

from app.db.database import get_db_connection
from app.schemas import CreateAlias


class AliasService:
    @staticmethod
    def add_alias(data: CreateAlias):
        data = data.model_dump() if isinstance(data, CreateAlias) else data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM aliases WHERE alias = %s;", (data["value"],))
        if cursor.fetchone() is not None:
            raise HTTPException(status_code=409, detail="Alias already exists")
        cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES  (%s,%s);", (data["id"], data["value"]))
        conn.commit()
        cursor.close()
        conn.close()