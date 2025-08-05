import psycopg2
from fastapi import APIRouter, HTTPException, Depends
from psycopg import AsyncConnection

from app.db.database import get_db_connection, get_db
from app.schemas import CategorieBase
from app.schemas.EditableClass import EditableField
from app.schemas.GraphData import Nodes, GraphData
from app.schemas.concept import ConceptResponse, ConceptName, RollbackConcept
from app.schemas.history import History
from app.schemas.mathematicien import MathematicienResponse
from app.schemas.pathcClass import UpdateConceptDict
from app.schemas.response import Response
from typing import List

from app.services.concept_service import ConceptService


router = APIRouter(prefix="", tags=["concepts"])



@router.get("/concept/{concept_id}", response_model=ConceptResponse)
async def getConcept(concept_id: int,db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).get_concept_info(concept_id)

@router.patch("/concept/rollback/{concept_id}")
async def rollbackConcept(concept_id: int,data: RollbackConcept,db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).rollback_history(concept_id,data)

@router.get("/getEditableFieldsOptions", response_model=EditableField)
async def getEditableFieldsOptions(db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).getEditableFieldsOptions()


@router.get("/concept/history/{concept_id}", response_model=List[History])
async def getHistory(concept_id: int,db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).get_concept_versions(concept_id)


@router.patch("/update/{concept_id}", response_model=Response)
async def updateConcept(concept_id: int, data: UpdateConceptDict,db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).updateConcept(concept_id, data)


@router.get("/getAllConceptName", response_model=List[ConceptName])
async def get_all_concept_name_R(db:AsyncConnection = Depends(get_db)):
    return await ConceptService(db).get_all_concepts_name()
