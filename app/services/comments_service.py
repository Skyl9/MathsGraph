import json
from datetime import datetime

from psycopg2 import DatabaseError
from psycopg2.extras import RealDictCursor

from app.db.database import get_db_connection


def serialize_row(row: dict) -> dict:
    return {
        key: (value.isoformat() if isinstance(value, datetime) else value)
        for key, value in row.items()
    }

class CommentsService:

    @staticmethod
    def get_comments(concept_id: int) -> list[dict]:
        try:

            conn = get_db_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
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
                result = cur.fetchall()
                res = [serialize_row(row) for row in result]
                print(res)
                return res
        except DatabaseError as e:
            print(f"Erreur de base de données : {e}")
            return []
        finally:
            conn.close()  # Toujours fermer la connexion

    @staticmethod
    def add_comment(
            concept_id: int,
            field: str,
            username: str | None,
            content: str,
            parent_id: int | None = None,

    ) -> dict:
        conn = get_db_connection()
        with conn.cursor() as cur:

            cur.execute("SELECT id FROM users WHERE username = %s;", (username,))
            user_id = cur.fetchone()[0] if username else None
            parent_id = None if parent_id==0 else parent_id
            print(parent_id)
            cur.execute(
                """
                INSERT INTO comments (concept_id, user_id, content, parent_id,field)
                VALUES (%s, %s, %s, %s,%s)
                RETURNING id, concept_id, user_id, content, created_at, updated_at,
                    parent_id, is_deleted, field
                """,
                (concept_id, user_id, content, parent_id,field),
            )
            print('Test 2')

            comment = cur.fetchone()
        conn.commit()
        return comment


    @staticmethod
    def update_comment(comment_id: int, content: str) -> dict:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT is_deleted FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = cur.fetchone()
            if not row or row[0]:
                raise ValueError("Commentaire introuvable ou supprimé")

        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                UPDATE public.comments
                SET content = %s,
                    updated_at = NOW()
                WHERE id = %s
                RETURNING id, concept_id, user_id, content, created_at, updated_at,
                    parent_id, is_deleted
                """,
                (content, comment_id),
            )
            updated = cur.fetchone()
        conn.commit()
        return updated

    @staticmethod
    def delete_comment(comment_id: int) -> None:
        conn = get_db_connection()
        print(comment_id)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT * FROM public.comments WHERE id = %s",
                (comment_id,),
            )
            row = cur.fetchone()
            print(row)
            if not row or not row[0]:
                raise ValueError("Commentaire introuvable ou déjà supprimé")
            cur.execute("UPDATE public.comments SET is_deleted = %s WHERE id = %s", (True,comment_id,))
        conn.commit()