from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import Response
from app.schemas.tags import TagsCreate, TagsUpdate, Tag
from app.services.tags_service import TagsService, logger

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("/id/concept_id/{concept_id}", summary="Récupère les IDs des tags d'un concept", response_model=Response[List[int]])
async def get_tags_ids(concept_id: int, db: AsyncConnection = Depends(get_db)):
    try:
        tags_ids = await TagsService(db).get_tags_id_by_concept_id(concept_id)
        logger.debug(f'Route GET /tags/id/concept_id/{concept_id} a renvoyé correctement : {tags_ids}')
        return {"error": None, "data": tags_ids, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /tags/id/concept_id/{concept_id} Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/name/concept_id/{concept_id}", summary="Récupère les noms et IDs des tags d'un concept",
            response_model=Response[List[Tag]])
async def get_tags_name_and_id(concept_id: int, db: AsyncConnection = Depends(get_db)):
    try:
        tags_data = await TagsService(db).get_tags_name_and_id_by_concept_id(concept_id)
        logger.debug(f'Route GET /tags/name/concept_id/{concept_id} a renvoyé correctement : {tags_data}')
        return {"error": None, "data": tags_data, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /tags/name/concept_id/{concept_id} Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.get("/all", summary="Récupère tous les tags", response_model=Response[List[Tag]])
async def get_all_tag(db: AsyncConnection = Depends(get_db)):
    try:
        all_tags = await TagsService(db).get_all_tags()
        logger.debug(f'Route GET /tags/all a renvoyé correctement : {all_tags}')
        return {"error": None, "data": all_tags, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route GET /tags/all Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.post("/concept", summary="Ajoute un tag à un concept", response_model=Response)
async def add_tag_concept(
    data: TagsUpdate, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await TagsService(db).add_tag_to_concept(data.concept_id, data.tag_id)
        logger.debug(
            f"Route POST /tags/add/concept a correctement ajouté le tag {data.tag_id} au concept {data.concept_id}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /tags/add/concept Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc


@router.delete("/concept/{concept_id}/tag/{tag_id}", summary="Supprime un tag d'un concept", response_model=Response)
async def remove_tag_concept(
        concept_id: int,
        tag_id: int,
        db: AsyncConnection = Depends(get_db),
        current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await TagsService(db).remove_tag_from_concept(concept_id, tag_id)

        logger.debug(
            f"Route DELETE /tags/concept/{concept_id}/tag/{tag_id} a correctement supprimé le tag {tag_id} du concept {concept_id}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /tags/remove/concept Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc

@router.post("", summary="Crée un nouveau tag", response_model=Response)
async def add_new_tag(
    data: TagsCreate, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await TagsService(db).create_new_tag(data.tag_name)
        logger.debug(f"Route POST /tags/add a correctement créé le tag : {data.tag_name}")
        return {"error": None, "data": None, "success": True, "meta": None}
    except InternalServerError as exc:
        logger.error(f"Route POST /tags/add Erreur : {exc}")
        raise InternalServerError(str(exc)) from exc
