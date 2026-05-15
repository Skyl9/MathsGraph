from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.core.exceptions import InternalServerError
from app.db.database import get_db
from app.schemas import CreateData, Response
from app.schemas.mathematicien import MathematicienResponse, MathematicienName
from app.services import MathematicienService
from app.services.mathematicien_service import logger

router = APIRouter(prefix="/mathematicien", tags=["mathematicien"])


@router.get("/{id_mathematicien}", response_model=Response[MathematicienResponse])
async def get_one_mathematicien_E(id_mathematicien: int, db: AsyncConnection = Depends(get_db)):
    try:
        oneMathematicien = await MathematicienService(db).get_one_mathematicien(id_mathematicien)
        logger.debug(f"Route GET {router.prefix}/{id_mathematicien} a renvoyé {oneMathematicien} mathematicien")
        return {"success": True, "data": oneMathematicien, "error": None,"meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur interne dans GET /{router.prefix}/{id_mathematicien} : %s", exc)
        raise InternalServerError(detail=str(exc))


@router.patch("/{id_mathematicien}", response_model=Response)
async def updateOneCategoryMathematicien_E(
    id_mathematicien: int, 
    data: dict, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await MathematicienService(db).update_mathematicien(id_mathematicien, data)
        logger.debug(f"Route PATCH {router.prefix}/update/{id_mathematicien} a été effectué avec succès")
        return {"success": True, "error": None,"meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur interne dans PATCH /{router.prefix}/update/{id_mathematicien} : %s", exc)
        raise InternalServerError(detail=str(exc))


@router.get("/", response_model=Response[List[MathematicienName]])
async def mathematicienName(db: AsyncConnection = Depends(get_db)):
    try:
        listMathematicien = await MathematicienService(db).get_all_mathematicien_name()
        logger.debug(f'Route GET {router.prefix}/mathematicien/ a renvoyé  la liste des mathematiciens')
        return {"success": True, "data": listMathematicien, "error": None,"meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur interne dans GET /mathematicien : %s", exc)
        raise InternalServerError(detail=str(exc))


@router.post('', response_model=Response)
async def add_mathematicien(
    data: CreateData, 
    db: AsyncConnection = Depends(get_db),
    current_user: dict = Depends(get_current_user_payload)
):
    try:
        async with db.transaction():
            await MathematicienService(db).add_mathematicien(data)
        logger.debug(f"Route Post {router.prefix}/create a créer avec succès un mathématicien")
        return {"success": True, "data": None, "error": None,"meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur interne dans POST /{router.prefix}/create : %s", exc)
        raise InternalServerError(detail=str(exc))


@router.get("/name/{name}", response_model=Response[MathematicienResponse])
async def get_mathematicien_by_name(name: str, db: AsyncConnection = Depends(get_db)):
    try:
        mathematicien_id = await MathematicienService(db).get_mathematicien_id(name)
        logger.debug(f"Route GET /{router.prefix}/name/{name} a renvoyé avec succès %d", mathematicien_id)
        return {"success": True, "data": mathematicien_id, "error": None,"meta": None}
    except InternalServerError as exc:
        logger.error(f"Erreur interne dans GET /{router.prefix}/name/{name} : %s", exc)
        raise InternalServerError(detail=str(exc))

@router.get("/timeline/all", summary="Récupère les données pour la frise chronologique", response_model=Response)
async def get_mathematiciens_timeline(db: AsyncConnection = Depends(get_db)):
    try:
        data = await MathematicienService(db).get_timeline_data()
        return {"success": True, "data": data, "error": None, "meta": None}
    except InternalServerError as exc:
        raise InternalServerError(detail=str(exc))