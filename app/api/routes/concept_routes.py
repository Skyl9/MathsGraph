from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response
from app.schemas.EditableClass import EditableField
from app.schemas.concept import ConceptResponse, ConceptName, RollbackConcept, ConceptCreate
from app.schemas.history import History
from app.schemas.patchClass import UpdateConceptDict
from app.services.concept_service import ConceptService, logger
from app.core.redis_client import redis_db
from fastapi.encoders import jsonable_encoder
import json

router = APIRouter(prefix="", tags=["concepts"])


@router.get(
    "/concept/{concept_id}",
    summary="Récupère les informations d'un concept",
    description="Retourne toutes les données associées à un concept spécifique via son identifiant.",
    response_model=Response[ConceptResponse],
)
async def get_concept(concept_id: int, db: AsyncSession = Depends(get_db)):
    cached_concept = None
    try:
        cached_concept = await redis_db.get(f"mathgraph:concept:{concept_id}")
    except Exception as e:
        logger.warning(f"⚠️ Impossible de se connecter à Redis. Le cache est ignoré. Erreur: {e}")

    if cached_concept:
        logger.debug(f"Concept {concept_id} servi depuis le cache Redis ⚡")
        return {"error": None, "data": json.loads(cached_concept), "success": True, "meta": {"source": "cache"}}

    concept = await ConceptService(db).get_concept_info(concept_id)

    try:
        json_concept = jsonable_encoder(concept)
        await redis_db.set(f"mathgraph:concept:{concept_id}", json.dumps(json_concept), ex=3600)  # cache court 1h
    except Exception as e:
        logger.warning(f"⚠️ Erreur lors de l'écriture dans Redis: {e}")

    logger.debug(f"Route GET /concept/{concept_id} a renvoyé correctement depuis la DB")
    return {"error": None, "data": concept, "success": True, "meta": {"source": "db"}}


@router.patch(
    "/concept/rollback/{concept_id}",
    summary="Annule une modification sur un concept",
    description="Restaure une version antérieure d'un concept en fonction de l'historique des modifications. Enregistre une nouvelle version pour la restauration.",
    response_model=Response,
)
async def rollback_concept(
    concept_id: int,
    data: RollbackConcept,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    data.username = str(current_user.get("sub", ""))
    await ConceptService(db).rollback_history(concept_id, data)
    logger.debug(
        f"Route PATCH /concept/rollback/{concept_id} a correctement rollback le concept dont l'id est:{concept_id}"
    )
    return {"error": None, "data": None, "success": True, "meta": None}


@router.post(
    "/concept",
    summary="Crée un nouveau concept",
    description="Ajoute un nouveau concept mathématique dans la base de données avec ses propriétés initiales.",
    response_model=Response,
)
async def create_concept_route(
    data: ConceptCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user_payload)
):
    result = await ConceptService(db).create_concept(data, str(current_user.get("sub", "")))
    logger.debug(f"Route POST /concept a créé le concept: {result['nom']}")
    return {"error": None, "data": result, "success": True, "meta": None}


@router.get(
    "/getEditableFieldsOptions",
    summary="Récupère les options des champs éditables",
    description="Fournit la configuration et les options disponibles pour l'édition des champs d'un concept sur le frontend.",
    response_model=Response[EditableField],
)
async def get_editable_fields_options(db: AsyncSession = Depends(get_db)):
    editable_field: EditableField = await ConceptService(db).get_editable_fields_options()
    logger.debug(
        f"Route GET /getEditableFieldsOptions a renvoyé correctement la liste des options : {str(editable_field)}"
    )
    return {"error": None, "data": editable_field, "success": True, "meta": None}


@router.get(
    "/concept/history/{concept_id}",
    summary="Historique des modifications d'un concept",
    description="Renvoie la liste chronologique de toutes les modifications effectuées sur un concept spécifique.",
    response_model=Response[List[History]],
)
async def get_history(concept_id: int, db: AsyncSession = Depends(get_db)):
    history_list: List[History] = await ConceptService(db).get_concept_versions(concept_id)
    logger.debug(
        f"Route /concept/history/{concept_id} a renvoyé correctement la list des versions: {str(history_list)}"
    )
    return {"error": None, "data": history_list, "success": True, "meta": None}


@router.patch(
    "/concept/{concept_id}",
    summary="Met à jour un concept",
    description="Modifie partiellement les champs d'un concept existant et enregistre la nouvelle version dans l'historique.",
    response_model=Response,
)
async def update_concept(
    concept_id: int,
    data: UpdateConceptDict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload),
):
    data.username = str(current_user.get("sub", ""))
    await ConceptService(db).updateConcept(concept_id, data)
    logger.debug(f"Route PATCH /update/{concept_id} a réussi la modification du concept dont l'id est:{concept_id}")
    return {"error": None, "data": None, "success": True, "meta": None}


@router.get(
    "/getAllConceptName",
    summary="Liste le nom de tous les concepts",
    description="Retourne une liste allégée contenant uniquement les identifiants et noms de tous les concepts disponibles.",
    response_model=Response[List[ConceptName]],
)
async def get_all_concept_name_r(db: AsyncSession = Depends(get_db)):
    concept_name_list: List[ConceptName] = await ConceptService(db).get_all_concepts_name()
    logger.debug(f"Route /getAllConceptName a renvoyé correctement la liste : {str(concept_name_list)}")
    return {"error": None, "data": concept_name_list, "success": True, "meta": None}


@router.get(
    "/recent-history",
    summary="Récupère le fil d'actualité global",
    description="Renvoie les dernières modifications effectuées sur l'ensemble des concepts, utile pour un fil d'actualité.",
    response_model=Response,
)
async def get_recent_history_route(limit: int = 20, db: AsyncSession = Depends(get_db)):
    history = await ConceptService(db).get_recent_history(limit)
    logger.debug(f"Route /recent-history a renvoyé correctement la liste : {str(history)}")
    return {"error": None, "data": history, "success": True, "meta": None}
