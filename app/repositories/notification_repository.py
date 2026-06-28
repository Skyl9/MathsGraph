from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID as PyUUID
from app.db.models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_unread_notifications(self, user_id: PyUUID):
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .order_by(Notification.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def mark_as_read(self, notification_id: int):
        stmt = (
            update(Notification).where(Notification.id == notification_id).values(is_read=True).returning(Notification)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one_or_none()

    async def mark_all_as_read(self, user_id: PyUUID):
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .values(is_read=True)
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def create_notification(self, user_id: PyUUID, message: str, concept_id: int | None = None):
        notif = Notification(user_id=user_id, message=message, concept_id=concept_id)
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif
