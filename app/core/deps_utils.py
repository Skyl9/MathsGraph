import psycopg
from psycopg import AsyncConnection


async def get_user_from_payload(payload: dict, db: AsyncConnection):
     email = payload.get("sub")
     if email:
         async with db.cursor(row_factory=psycopg.rows.dict_row) as cur:
             await cur.execute("SELECT id, username, email, is_active FROM users WHERE email = %s", (email,))
             return await cur.fetchone()
     return None