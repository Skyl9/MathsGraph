from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID as PyUUID
from app.repositories.notification_repository import NotificationRepository
from app.core.exceptions import NotFoundException


class NotificationService:
    def __init__(self, db: AsyncSession):
        self.repo = NotificationRepository(db)

    async def get_unread_notifications(self, user_id: PyUUID):
        return await self.repo.get_unread_notifications(user_id)

    async def mark_as_read(self, notification_id: int):
        notif = await self.repo.mark_as_read(notification_id)
        if not notif:
            raise NotFoundException(detail="Notification introuvable")
        return notif

    async def mark_all_as_read(self, user_id: PyUUID):
        await self.repo.mark_all_as_read(user_id)

    async def create_notification(self, user_id: PyUUID, message: str, concept_id: int | None = None):
        return await self.repo.create_notification(user_id, message, concept_id)
