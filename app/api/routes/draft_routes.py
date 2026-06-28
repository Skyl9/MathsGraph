from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_current_user
from app.db.database import get_db
from app.schemas.draft import DraftCreate, DraftUpdate, DraftResponse
from app.schemas.response import Response
from app.services.draft_service import DraftService
from app.db.models import User

router = APIRouter()


@router.get("/me", response_model=Response[List[DraftResponse]], summary="Récupérer mes brouillons")
async def get_my_drafts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    drafts = await DraftService(db).get_my_drafts(current_user.id)
    return {"error": None, "data": drafts, "success": True, "meta": None}


@router.get("/{draft_id}", response_model=Response[DraftResponse], summary="Récupérer un brouillon")
async def get_draft(draft_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    draft = await DraftService(db).get_draft(draft_id, current_user.id)
    return {"error": None, "data": draft, "success": True, "meta": None}


@router.post("/", response_model=Response[DraftResponse], summary="Créer un brouillon")
async def create_draft(
    data: DraftCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    draft = await DraftService(db).create_draft(current_user.id, data)
    return {"error": None, "data": draft, "success": True, "meta": None}


@router.patch("/{draft_id}", response_model=Response[DraftResponse], summary="Modifier un brouillon")
async def update_draft(
    draft_id: int, data: DraftUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    draft = await DraftService(db).update_draft(draft_id, current_user.id, data)
    return {"error": None, "data": draft, "success": True, "meta": None}


@router.post("/{draft_id}/publish", response_model=Response[dict], summary="Publier un brouillon")
async def publish_draft(
    draft_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    res = await DraftService(db).publish_draft(draft_id, current_user.id, current_user.username)
    return {"error": None, "data": res, "success": True, "meta": None}


@router.delete("/{draft_id}", response_model=Response[dict], summary="Supprimer un brouillon")
async def delete_draft(
    draft_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    await DraftService(db).delete_draft(draft_id, current_user.id)
    return {"error": None, "data": {"message": "Brouillon supprimé"}, "success": True, "meta": None}
