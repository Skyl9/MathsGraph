from typing import List, Any

from fastapi import APIRouter, HTTPException
from app.services.comments_service import CommentsService
from app.schemas.comments import CommentIn, CommentUpdate, CommentResponse

router = APIRouter(prefix="/comments", tags=["comments"])


@router.get("/{concept_id}", summary="Récupère les commentaires d'un concept",response_model=List[CommentResponse])
async def get_comments(concept_id: int):
    print("fetch Comments")
    return CommentsService.get_comments(concept_id)


@router.post("/add/{concept_id}", summary="Ajoute un commentaire à un concept")
async def post_comment(concept_id:int, data: CommentIn):
    print(data)
    try:
        return CommentsService.add_comment(
            concept_id=concept_id,
            username=data.username,
            content=data.content,
            parent_id=data.parent_id,
            field = data.field
        )
    except Exception as e:
        raise e #HTTPException(status_code=400, detail=str(e))


@router.patch("/update/{comment_id}", summary="Met à jour le contenu d'un commentaire")
async def update_comment(comment_id: int,data: CommentUpdate,):
    try:
        return CommentsService.update_comment(comment_id, data.content)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/delete/{comment_id}", summary="Supprime un commentaire")
async def delete_comment(comment_id: int):
    try:
        return CommentsService.delete_comment(comment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))