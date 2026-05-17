from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response
from app.schemas.comments import CommentIn, CommentUpdate, CommentResponse
from app.services.comments_service import CommentsService, logger

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/recent", summary="Récupère les derniers commentaires globaux", response_model=Response)
async def get_recent_comments_route(limit: int = 20, db: AsyncSession = Depends(get_db)):
    comments = await CommentsService(db).get_recent_comments(limit)
    return {"error": None, "data": comments, "success": True, "meta": None}


@router.get("/{concept_id}", summary="Récupère les commentaires d'un concept", response_model=Response[List[CommentResponse]])
async def get_comments(concept_id: int, db: AsyncSession = Depends(get_db)):
    comments: List[CommentResponse] = await CommentsService(db).get_comments(concept_id)
    logger.debug(f'Route GET /comments/{concept_id} a renvoyé correctement : {str(comments)}')
    return {"error": None, "data": comments, "success": True, "meta": None}


@router.post("/{concept_id}", summary="Ajoute un commentaire à un concept", response_model=Response)
async def post_comment(
    concept_id: int, 
    data: CommentIn, 
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    await CommentsService(db).add_comment(
        concept_id=concept_id,
        username=data.username,
        content=data.content,
        parent_id=data.parent_id,
        field=data.field
    )
    await db.commit()
    logger.debug(f"Route POST /comments/add/{concept_id} a correctement ajouté un commentaire au concept d'id : {concept_id}")
    return {"error": None, "data": None, "success": True, "meta": None}


@router.patch("/{comment_id}", summary="Met à jour le contenu d'un commentaire", response_model=Response)
async def update_comment(comment_id: int, data: CommentUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)):
    await CommentsService(db).update_comment(comment_id, data.content, current_user)
    await db.commit()
    logger.debug(f"Route PATCH /comments/update/{comment_id} a correctement mis à jour le commentaire d'id : {comment_id}")
    return {"error": None, "data": None, "success": True, "meta": None}


@router.delete("/{comment_id}", summary="Supprime un commentaire", response_model=Response)
async def delete_comment(comment_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)):
    await CommentsService(db).delete_comment(comment_id, current_user)
    await db.commit()
    logger.debug(f"Route DELETE /comments/delete/{comment_id} a correctement supprimé le commentaire d'id : {comment_id}")
    return {"error": None, "data": None, "success": True, "meta": None}
