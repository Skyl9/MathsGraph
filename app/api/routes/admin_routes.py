from fastapi import APIRouter

from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["alias"])

@router.get("/stats")
async def get_stats():
    return AdminService.get_stats()

@router.get("/users")
async def get_users():
    return AdminService.get_users()

@router.get("/contents")
async def get_contents():
    return AdminService.get_contents()