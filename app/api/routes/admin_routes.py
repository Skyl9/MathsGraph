from psycopg import AsyncConnection
from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["alias"])

@router.get("/stats")
async def get_stats(db: AsyncConnection = Depends(get_db)):
    return await AdminService(db).get_stats()

@router.get("/users")
async def get_users(db: AsyncConnection = Depends(get_db)):
    return await AdminService(db).get_users()

@router.get("/contents")
async def get_contents(db: AsyncConnection = Depends(get_db)):
    return await AdminService(db).get_contents()