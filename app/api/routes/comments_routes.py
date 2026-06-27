from typing import List

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.core.limiter import limiter
from app.db.database import get_db
from app.schemas import Response
from app.schemas.comments import CommentIn, CommentUpdate, CommentResponse
from app.services.comments_service import CommentsService, logger

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get(
    "/recent",
    summary="Récupère les derniers commentaires globaux",
    description="Retourne une liste des commentaires les plus récents sur l'ensemble des concepts. Le nombre de commentaires retournés peut être limité avec le paramètre 'limit'.",
    response_model=Response,
)
async def get_recent_comments_route(limit: int = 20, db: AsyncSession = Depends(get_db)):
    comments = await CommentsService(db).get_recent_comments(limit)
    return {"error": None, "data": comments, "success": True, "meta": None}


@router.get(
    "/{concept_id}",
    summary="Récupère les commentaires d'un concept",
    description="Retourne la liste complète des commentaires associés à un identifiant de concept spécifique.",
    response_model=Response[List[CommentResponse]],
)
async def get_comments(concept_id: int, db: AsyncSession = Depends(get_db)):
    comments = await CommentsService(db).get_comments(concept_id)
    logger.debug(f"Route GET /comments/{concept_id} a renvoyé correctement : <data_omitted>")
    return {"error": None, "data": comments, "success": True, "meta": None}


@router.post(
    "/{concept_id}",
    status_code=201,
    summary="Ajoute un commentaire à un concept",
    description="Crée un nouveau commentaire et l'associe à un concept précis. Nécessite d'être authentifié.",
    response_model=Response,
)
@limiter.limit("20/minute")
async def post_comment(
    request: Request,
    concept_id: int,
    data: CommentIn,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await CommentsService(db).add_comment(
        concept_id=concept_id, username=data.username, content=data.content, parent_id=data.parent_id, field=data.field
    )
    await db.commit()
    logger.debug(
        f"Route POST /comments/add/{concept_id} a correctement ajouté un commentaire au concept d'id : {concept_id}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.patch(
    "/{comment_id}",
    summary="Met à jour le contenu d'un commentaire",
    description="Modifie le contenu textuel d'un commentaire existant à partir de son identifiant. L'utilisateur doit être l'auteur du commentaire ou avoir les droits suffisants.",
    response_model=Response,
)
async def update_comment(
    comment_id: int,
    data: CommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await CommentsService(db).update_comment(comment_id, data.content, current_user)
    await db.commit()
    logger.debug(
        f"Route PATCH /comments/update/{comment_id} a correctement mis à jour le commentaire d'id : {comment_id}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.delete(
    "/{comment_id}",
    status_code=204,
    summary="Supprime un commentaire",
    description="Supprime un commentaire spécifique en utilisant son identifiant. Seul l'auteur ou un administrateur peut effectuer cette action.",
)
async def delete_comment(
    comment_id: int, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await CommentsService(db).delete_comment(comment_id, current_user)
    await db.commit()
    logger.debug(
        f"Route DELETE /comments/delete/{comment_id} a correctement supprimé le commentaire d'id : {comment_id}"
    )
    return None
