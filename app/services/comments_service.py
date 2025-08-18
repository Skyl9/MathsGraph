from psycopg import AsyncConnection
from psycopg import DatabaseError

from app.core.exceptions import NotFoundException

import logging

logger = logging.getLogger(__name__)

class CommentsService:

    def __init__(self,db:AsyncConnection):
        self.db = db


    async def get_comments(self,concept_id: int) -> list[dict]:
        try:

           async with self.db.cursor() as cur:
                await cur.execute(
                    """
                    SELECT comments.id,
                           comments.concept_id,
                           comments.user_id,
                           comments.content,
                           comments.created_at,
                           comments.updated_at,
                           comments.parent_id,
                           comments.is_deleted,
                           comments.field,
                           users.username
                    FROM public.comments
                             LEFT JOIN
                         public.users ON comments.user_id = users.id

                    WHERE comments.concept_id = %s
                      AND comments.is_deleted = false
                    ORDER BY comments.created_at ASC
                    """,
                    (concept_id,),
                )
                result = await cur.fetchall()
                res = []
                for row in result:
                    res.append(
                        {
                            "id": row[0],
                            "concept_id": row[1],
                            "user_id": row[2],
                            "content": row[3],
                            "created_at": row[4],
                            "updated_at": row[5],
                            "parent_id": row[6],
                            "is_deleted": row[7],
                            "field": row[8],
                            "username": row[9],
                        }
                    )
                return res
        except DatabaseError as e:
            print(f"Erreur de base de données : {e}")
            return []


    async def add_comment(
            self,
            concept_id: int,
            field: str,
            username: str | None,
            content: str,
            parent_id: int | None = None,

    ) -> dict:
        async with (self.db.cursor() as cur):

            await cur.execute("SELECT id FROM users WHERE username = %s;", (username,))
            user_id = await cur.fetchone()
            user_id=user_id[0] if username else None
            if not user_id:
                raise NotFoundException(detail="Utilisateur introuvable")
            parent_id = None if parent_id==0 else parent_id
            await cur.execute("SELECT id FROM concepts WHERE id = %s", (concept_id,))
            if not await cur.fetchone():
                raise NotFoundException(detail="Concept introuvable")
            await cur.execute(
                """
                INSERT INTO comments (concept_id, user_id, content, parent_id,field)
                VALUES (%s, %s, %s, %s,%s)
                RETURNING id, concept_id, user_id, content, created_at, updated_at,
                    parent_id, is_deleted, field
                """,
                (concept_id, user_id, content, parent_id,field),
            )

            comment = await cur.fetchone()
        return comment



    async def update_comment(self,comment_id: int, content: str) -> dict:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT is_deleted FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = await cur.fetchone()
            if not row or row[0]:
                raise NotFoundException(detail="Commentaire introuvable ou supprimé")

            await cur.execute(
                """
                UPDATE public.comments
                SET content = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, concept_id, user_id, content, created_at, updated_at,
                    parent_id, is_deleted,field
                """,
                (content, comment_id),
            )
            data = await cur.fetchone()
            updated = {
                "id":data[0],
                "concept_id": data[1],
                "user_id": data[2],
                "content": data[3],
                "created_at": data[4],
                "updated_at": data[5],
                "parent_id": data[6],
                "is_deleted": data[7],
                "field":data[8]
            }
        return updated


    async def delete_comment(self,comment_id: int) -> None:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT is_deleted FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = await cur.fetchone()

            if not row:
                raise NotFoundException("Commentaire introuvable")
            if row[0]:
                raise NotFoundException("Commentaire déjà supprimé")

            await cur.execute("UPDATE public.comments SET is_deleted = %s WHERE id = %s", (True,comment_id,))
