from psycopg2 import sql

from app.core.exceptions import NotFoundException
from app.db.database import get_db_connection
from app.schemas.type import TypeResponse, TypeUpdate, TypeNom

class TypeService:
    @staticmethod
    def get_all_type_name() -> list[TypeNom]:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, type FROM type")
            types_fetched = cur.fetchall()
            return [{"id": i[0], "type": i[1]} for i in types_fetched]
        finally:
            conn.close()

    @staticmethod
    def get_one_type(id_type: int) -> TypeResponse:
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT * FROM type WHERE id = %s", (id_type,))
            type_fetched = cur.fetchone()
            if not type_fetched:
                raise NotFoundException(f"Type with ID {id_type} not found")
            return {
                "id": type_fetched[0],
                "type": type_fetched[1],
            }
        finally:
            conn.close()

    @staticmethod
    def update_type(id_type: int, data: TypeUpdate):
        allowed_fields = {"type"}
        field = data["field"]

        if field not in allowed_fields:
            raise ValueError(
                f"Le champ '{field}' n'est pas autorisé pour une mise à jour."
            )

        conn = get_db_connection()
        try:
            cur = conn.cursor()
            query = sql.SQL(f"UPDATE type SET {field} = %s WHERE id = %s").format(
                field=sql.Identifier(field)
            )
            cur.execute(query, (data["value"], id_type))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
