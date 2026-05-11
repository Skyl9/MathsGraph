from psycopg import AsyncConnection
from psycopg import DatabaseError

from app.core.exceptions import NotFoundException, ForbiddenException
import logging
from app.utils.db_utils import check_exists, get_id_by_field

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
        user_id = await get_id_by_field(self.db, "users", "username", username, "Utilisateur introuvable")

        async with (self.db.cursor() as cur):
            parent_id = None if parent_id==0 else parent_id

            await check_exists(self.db, "concepts", concept_id, "Concept introuvable")

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

    async def update_comment(self, comment_id: int, content: str, current_user: dict) -> dict:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT user_id, is_deleted FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = await cur.fetchone()
            if not row or row[1]:
                raise NotFoundException(detail="Commentaire introuvable ou supprimé")

            comment_user_id = int(row[0])
            token_user_id = int(current_user.get("id"))

            is_author = (token_user_id == comment_user_id)
            is_admin = current_user.get("role") in ["admin", "moderator"]

            if not (is_author or is_admin):
                raise ForbiddenException(detail="Vous n'êtes pas autorisé à modifier ce commentaire.")

            await cur.execute(
                """
                UPDATE public.comments
                SET content    = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, concept_id, user_id, content, created_at, updated_at, parent_id, is_deleted, field
                """,
                (content, comment_id),
            )
            data = await cur.fetchone()
            return {
                "id": data[0], "concept_id": data[1], "user_id": data[2], "content": data[3],
                "created_at": data[4], "updated_at": data[5], "parent_id": data[6],
                "is_deleted": data[7], "field": data[8]
            }

    async def delete_comment(self, comment_id: int, current_user: dict) -> None:
        async with self.db.cursor() as cur:
            await cur.execute(
                "SELECT user_id, is_deleted FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = await cur.fetchone()

            if not row:
                raise NotFoundException("Commentaire introuvable")
            if row[1]:
                raise NotFoundException("Commentaire déjà supprimé")

            comment_user_id = int(row[0])
            token_user_id = int(current_user.get("id"))

            is_author = (token_user_id == comment_user_id)
            is_admin = current_user.get("role") in ["admin", "moderator"]

            if not (is_author or is_admin):
                raise ForbiddenException("Vous n'êtes pas autorisé à supprimer ce commentaire.")

            await cur.execute("UPDATE public.comments SET is_deleted = true WHERE id = %s", (comment_id,))


    async def get_recent_comments(self, limit: int = 20) -> list[dict]:
        async with self.db.cursor() as cursor:
            await cursor.execute("""
                                 SELECT c.id,
                                        c.concept_id,
                                        co.nom as concept_nom,
                                        c.user_id,
                                        u.username,
                                        c.content,
                                        c.created_at,
                                        c.field
                                 FROM comments c
                                          JOIN users u ON c.user_id = u.id
                                          JOIN concepts co ON c.concept_id = co.id
                                 WHERE c.is_deleted = false
                                 ORDER BY c.created_at DESC
                                 LIMIT %s
                                 """, (limit,))
            data = await cursor.fetchall()

            return [{
                "id": row[0],
                "concept_id": row[1],
                "concept_nom": row[2],
                "user_id": row[3],
                "username": row[4],
                "content": row[5],
                "created_at": row[6].isoformat() if row[6] else None,
                "field": row[7]
            } for row in data]