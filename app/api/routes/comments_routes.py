from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_active_user, get_current_user_payload
from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response
from app.schemas.comments import CommentIn, CommentUpdate, CommentResponse
from app.services.comments_service import CommentsService, logger

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/recent", summary="Récupère les derniers commentaires globaux", response_model=Response)
async def get_recent_comments_route(limit: int = 20, db: AsyncConnection = Depends(get_db)):
    try:
        comments = await CommentsService(db).get_recent_comments(limit)
        return {"error": None, "data": comments, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /comments/recent Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/{concept_id}", summary="Récupère les commentaires d'un concept", response_model=Response[List[CommentResponse]])
async def get_comments(concept_id: int, db: AsyncConnection = Depends(get_db)):
    try:
        comments: List[CommentResponse] = await CommentsService(db).get_comments(concept_id)
        logger.debug(f'Route GET /comments/{concept_id} a renvoyé correctement : {str(comments)}')
        return {"error": None, "data": comments, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /comments/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.post("/{concept_id}", summary="Ajoute un commentaire à un concept", response_model=Response)
async def post_comment(
    concept_id: int, 
    data: CommentIn, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await CommentsService(db).add_comment(
                concept_id=concept_id,
                username=data.username,
                content=data.content,
                parent_id=data.parent_id,
                field=data.field
            )
        logger.debug(f"Route POST /comments/add/{concept_id} a correctement ajouté un commentaire au concept d'id : {concept_id}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /comments/add/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.patch("/{comment_id}", summary="Met à jour le contenu d'un commentaire", response_model=Response)
async def update_comment(comment_id: int, data: CommentUpdate, db: AsyncConnection = Depends(get_db),current_user: dict = Depends(get_current_user_payload)):
    try:
        async with db.transaction():
            await CommentsService(db).update_comment(comment_id, data.content, current_user)
        logger.debug(f"Route PATCH /comments/update/{comment_id} a correctement mis à jour le commentaire d'id : {comment_id}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route PATCH /comments/update/{comment_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.delete("/{comment_id}", summary="Supprime un commentaire", response_model=Response)
async def delete_comment(comment_id: int, db: AsyncConnection = Depends(get_db),current_user: dict = Depends(get_current_user_payload)):
    try:
        async with db.transaction():
            await CommentsService(db).delete_comment(comment_id, current_user)
        logger.debug(f"Route DELETE /comments/delete/{comment_id} a correctement supprimé le commentaire d'id : {comment_id}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route DELETE /comments/delete/{comment_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc
