from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.deps import get_current_user_payload
from app.db.database import get_db
from app.schemas import Response
from app.schemas.EditableClass import EditableField
from app.schemas.concept import ConceptResponse, ConceptName, RollbackConcept
from app.schemas.history import History
from app.schemas.pathcClass import UpdateConceptDict
from app.services.concept_service import ConceptService,logger

router = APIRouter(prefix="", tags=["concepts"])


@router.get("/concept/{concept_id}", response_model=Response[ConceptResponse])
async def getConcept(concept_id: int, db: AsyncConnection = Depends(get_db)):
    concept:ConceptResponse= await ConceptService(db).get_concept_info(concept_id)
    logger.debug(f'Route GET /concept/{concept_id} a renvoyé correctement : {str(concept)}')
    return {"error":None,"data":concept,"success":True,"meta":None}


@router.patch("/concept/rollback/{concept_id}",response_model=Response)
async def rollbackConcept(concept_id: int, data: RollbackConcept, db: AsyncConnection = Depends(get_db),current_user: dict = Depends(get_current_user_payload)):
    data.username = current_user.get("sub")
    async with db.transaction():
        await ConceptService(db).rollback_history(concept_id, data)
    logger.debug(f"Route PATCH /concept/rollback/{concept_id} a correctement rollback le concept dont l'id est:{concept_id}")
    return {"error":None,"data":None,"success":True,"meta":None}


@router.get("/getEditableFieldsOptions", response_model=Response[EditableField])
async def getEditableFieldsOptions(db: AsyncConnection = Depends(get_db)):
    editableField:EditableField =  await ConceptService(db).getEditableFieldsOptions()
    logger.debug(f'Route GET /getEditableFieldsOptions a renvoyé correctement la liste des options : {str(editableField)}')
    return {"error":None,"data":editableField,"success":True,"meta":None}


@router.get("/concept/history/{concept_id}", response_model=Response[List[History]])
async def getHistory(concept_id: int, db: AsyncConnection = Depends(get_db)):
    historyList:List[History] = await ConceptService(db).get_concept_versions(concept_id)
    logger.debug(f'Route /concept/history/{concept_id} a renvoyé correctement la list des versions: {str(historyList)}')
    return {"error":None,"data":historyList,"success":True,"meta":None}


@router.patch("/concept/{concept_id}",response_model=Response)
async def updateConcept(concept_id: int, data: UpdateConceptDict, db: AsyncConnection = Depends(get_db),current_user: dict = Depends(get_current_user_payload)):
    data.username = current_user.get("sub")
    async with db.transaction():
        await ConceptService(db).updateConcept(concept_id, data)
    logger.debug(f"Route PATCH /update/{concept_id} a réussi la modification du concept dont l'id est:{concept_id}")
    return {"error":None,"data":None,"success":True,"meta":None}


@router.get("/getAllConceptName", response_model=Response[List[ConceptName]])
async def get_all_concept_name_R(db: AsyncConnection = Depends(get_db)):
    conceptNameList:List[ConceptName]= await ConceptService(db).get_all_concepts_name()
    logger.debug(f'Route /getAllConceptName a renvoyé correctement la liste : {str(conceptNameList)}')
    return {"error":None,"data":conceptNameList,"success":True,"meta":None}

@router.get("/recent-history", summary="Récupère le fil d'actualité global", response_model=Response)
async def get_recent_history_route(limit: int = 20, db: AsyncConnection = Depends(get_db)):
    history = await ConceptService(db).get_recent_history(limit)
    logger.debug(f'Route /recent-history a renvoyé correctement la liste : {str(history)}')
    return {"error": None, "data": history, "success": True, "meta": None}
