from fastapi import APIRouter, Depends
from psycopg import AsyncConnection

from app.db.database import get_db
from app.schemas.tags import TagsCreate, TagsUpdate
from app.services.tags_service import TagsService

router = APIRouter(prefix="/tags", tags=["tags"])

@router.get("/id/concept_id/{concept_id}")
async def get_tags_ids(concept_id: int,db:AsyncConnection=Depends(get_db)):
    return await TagsService(db).get_tags_id_by_concept_id(concept_id)

@router.get("/name/concept_id/{concept_id}")
async def get_tags_name_and_id(concept_id: int,db:AsyncConnection=Depends(get_db)):
   return await TagsService(db).get_tags_name_and_id_by_concept_id(concept_id)

@router.get("/all")
async def get_all_tag(db:AsyncConnection=Depends(get_db)):
    return await TagsService(db).get_all_tags()

@router.post("/add/concept")
async def add_tag_concept(data : TagsUpdate,db:AsyncConnection=Depends(get_db)):
    return await TagsService(db).add_tag_to_concept(data.concept_id,data.tag_id)

@router.post("/remove/concept")
async def remove_tag_concept(data : TagsUpdate,db:AsyncConnection=Depends(get_db)):
    return await TagsService(db).remove_tag_from_concept(data.concept_id,data.tag_id)
@router.post("/add")
async def add_new_tag(data:TagsCreate,db:AsyncConnection=Depends(get_db)):
    return await TagsService(db).create_new_tag(data.tag_name)