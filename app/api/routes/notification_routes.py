from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.deps import get_current_user
from app.db.database import get_db
from app.schemas.notification import NotificationResponse
from app.schemas.response import Response
from app.services.notification_service import NotificationService

router = APIRouter()


@router.get(
    "/notifications",
    response_model=Response[List[NotificationResponse]],
    summary="Récupérer les notifications non lues",
)
async def get_unread_notifications(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    notifs = await NotificationService(db).get_unread_notifications(current_user.id)
    return {"error": None, "data": notifs, "success": True, "meta": None}


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=Response[NotificationResponse],
    summary="Marquer une notification comme lue",
)
async def mark_notification_read(
    notification_id: int, db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)
):
    notif = await NotificationService(db).mark_as_read(notification_id)
    return {"error": None, "data": notif, "success": True, "meta": None}


@router.patch(
    "/notifications/read-all", response_model=Response[str], summary="Marquer toutes les notifications comme lues"
)
async def mark_all_notifications_read(db: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    await NotificationService(db).mark_all_as_read(current_user.id)
    return {
        "error": None,
        "data": "Toutes les notifications ont été marquées comme lues",
        "success": True,
        "meta": None,
    }
