from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response
from app.schemas.tags import TagsCreate, TagsUpdate, Tag
from app.services.tags_service import TagsService, logger

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "/id/concept_id/{concept_id}",
    summary="Récupère les IDs des tags d'un concept",
    description="Retourne la liste des identifiants (IDs) des tags qui sont associés à un concept spécifique.",
    response_model=Response[List[int]],
)
async def get_tags_ids(concept_id: int, db: AsyncSession = Depends(get_db)):
    tags_ids = await TagsService(db).get_tags_id_by_concept_id(concept_id)
    logger.debug(f"Route GET /tags/id/concept_id/{concept_id} a renvoyé correctement : {tags_ids}")
    return {"error": None, "data": tags_ids, "success": True, "meta": None}


@router.get(
    "/name/concept_id/{concept_id}",
    summary="Récupère les noms et IDs des tags d'un concept",
    description="Retourne une liste contenant à la fois les identifiants et les noms des tags associés à un concept donné.",
    response_model=Response[List[Tag]],
)
async def get_tags_name_and_id(concept_id: int, db: AsyncSession = Depends(get_db)):
    tags_data = await TagsService(db).get_tags_name_and_id_by_concept_id(concept_id)
    logger.debug(f"Route GET /tags/name/concept_id/{concept_id} a renvoyé correctement : {tags_data}")
    return {"error": None, "data": tags_data, "success": True, "meta": None}


@router.get(
    "/all",
    summary="Récupère tous les tags",
    description="Retourne la liste exhaustive de tous les tags existants dans le système.",
    response_model=Response[List[Tag]],
)
async def get_all_tag(db: AsyncSession = Depends(get_db)):
    all_tags = await TagsService(db).get_all_tags()
    logger.debug(f"Route GET /tags/all a renvoyé correctement : {all_tags}")
    return {"error": None, "data": all_tags, "success": True, "meta": None}


@router.post(
    "/concept",
    summary="Ajoute un tag à un concept",
    description="Associe un tag existant à un concept spécifique en utilisant les données fournies. Nécessite une authentification.",
    response_model=Response,
)
async def add_tag_concept(
    data: TagsUpdate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await TagsService(db).add_tag_to_concept(data.concept_id, data.tag_id, current_user)
    await db.commit()
    logger.debug(
        f"Route POST /tags/add/concept a correctement ajouté le tag {data.tag_id} au concept {data.concept_id}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.delete(
    "/concept/{concept_id}/tag/{tag_id}",
    summary="Supprime un tag d'un concept",
    description="Retire l'association entre un tag et un concept sans supprimer le tag lui-même. Action réservée aux utilisateurs autorisés.",
    response_model=Response,
)
async def remove_tag_concept(
    concept_id: int,
    tag_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    await TagsService(db).remove_tag_from_concept(concept_id, tag_id, current_user)
    await db.commit()
    logger.debug(
        f"Route DELETE /tags/concept/{concept_id}/tag/{tag_id} a correctement supprimé le tag {tag_id} du concept {concept_id}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.post(
    "",
    summary="Crée un nouveau tag",
    description="Ajoute un tout nouveau tag dans la base de données globale. Nécessite d'être connecté.",
    response_model=Response,
)
async def add_new_tag(
    data: TagsCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    await TagsService(db).create_new_tag(data.tag_name, current_user)
    await db.commit()
    logger.debug(f"Route POST /tags/add a correctement créé le tag : {data.tag_name}")
    return {"error": None, "data": None, "success": True, "meta": None}
