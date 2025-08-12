from typing import List

from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.core.exceptions import InternalServerError
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
    try:
        concept:ConceptResponse= await ConceptService(db).get_concept_info(concept_id)
        logger.debug(f'Route GET /concept/{concept_id} a renvoyé correctement : {str(concept)}')
        return {"error":None,"data":concept,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route GET /concept/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.patch("/concept/rollback/{concept_id}",response_model=Response)
async def rollbackConcept(concept_id: int, data: RollbackConcept, db: AsyncConnection = Depends(get_db)):
    try:
        await ConceptService(db).rollback_history(concept_id, data)
        logger.debug(f"Route PATCH /concept/rollback/{concept_id} a correctement rollback le concept dont l'id est:{concept_id}")
        return {"error":None,"data":None,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route PATCH /concept/rollback/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/getEditableFieldsOptions", response_model=Response[EditableField])
async def getEditableFieldsOptions(db: AsyncConnection = Depends(get_db)):
    try:
        editableField:EditableField =  await ConceptService(db).getEditableFieldsOptions()
        logger.debug(f'Route GET /getEditableFieldsOptions a renvoyé correctement la liste des options : {str(editableField)}')
        return {"error":None,"data":editableField,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route GET /getEditableFieldsOptions Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/concept/history/{concept_id}", response_model=Response[List[History]])
async def getHistory(concept_id: int, db: AsyncConnection = Depends(get_db)):
    try:
        historyList:List[History] = await ConceptService(db).get_concept_versions(concept_id)
        logger.debug(f'Route /concept/history/{concept_id} a renvoyé correctement la list des versions: {str(historyList)}')
        return {"error":None,"data":historyList,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route GET /concept/history/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.patch("/update/{concept_id}",response_model=Response)
async def updateConcept(concept_id: int, data: UpdateConceptDict, db: AsyncConnection = Depends(get_db)):
    try:
        await ConceptService(db).updateConcept(concept_id, data)
        logger.debug(f"Route PATCH /update/{concept_id} a réussi la modification du concept dont l'id est:{concept_id}")
        return {"error":None,"data":None,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route PATCH /update/{concept_id} Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc


@router.get("/getAllConceptName", response_model=Response[List[ConceptName]])
async def get_all_concept_name_R(db: AsyncConnection = Depends(get_db)):
    try:
        conceptNameList:List[ConceptName]= ConceptService(db).get_all_concepts_name()
        logger.debug(f'Route /getAllConceptName a renvoyé correctement la liste : {str(conceptNameList)}')
        return {"error":None,"data":conceptNameList,"success":True,"meta":None}
    except InternalServerError as exc:
        logger.error(f"Route GET /getAllConceptName Erreur : {str(exc)}")
        raise InternalServerError(str(exc)) from exc
