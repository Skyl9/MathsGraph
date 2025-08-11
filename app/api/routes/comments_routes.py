from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas.comments import CommentIn, CommentUpdate, CommentResponse
from app.services.comments_service import CommentsService

router = APIRouter(prefix="/comments", tags=["comments"])


# TODO Prendre en compte les erreur coté backend commentaire => implémenter dans service pas routes (A voir si pas mieux global)
@router.get("/{concept_id}", summary="Récupère les commentaires d'un concept", response_model=List[CommentResponse])
async def get_comments(concept_id: int, db: AsyncConnection = Depends(get_db)):
    return await CommentsService(db).get_comments(concept_id)


@router.post("/add/{concept_id}", summary="Ajoute un commentaire à un concept")
async def post_comment(concept_id: int, data: CommentIn, db: AsyncConnection = Depends(get_db)):
    return await CommentsService(db).add_comment(
        concept_id=concept_id,
        username=data.username,
        content=data.content,
        parent_id=data.parent_id,
        field=data.field
    )


@router.patch("/update/{comment_id}", summary="Met à jour le contenu d'un commentaire")
async def update_comment(comment_id: int, data: CommentUpdate, db: AsyncConnection = Depends(get_db)):
    return await CommentsService(db).update_comment(comment_id, data.content)


@router.delete("/delete/{comment_id}", summary="Supprime un commentaire")
async def delete_comment(comment_id: int, db: AsyncConnection = Depends(get_db)):
    return await CommentsService(db).delete_comment(comment_id)
