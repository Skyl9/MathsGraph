import logging
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.admin_repository import AdminRepository

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.repo = AdminRepository(db)

    async def get_stats(self):
        return await self.repo.get_stats()

    async def get_users(self, skip: int = 0, limit: int = 50):
        result = await self.repo.get_users(skip, limit)

        return {
            "items": [
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "role": u.role,
                    "is_active": u.is_active,
                    "created_at": u.created_at,
                }
                for u in result["items"]
            ],
            "total": result["total"],
        }

    async def get_concepts_admin(self, skip: int = 0, limit: int = 50):
        result = await self.repo.get_concepts_admin(skip, limit)

        return {
            "items": [
                {
                    "id": c.id,
                    "nom": c.nom,
                    "type": c.type.type if c.type else None,
                }
                for c in result["items"]
            ],
            "total": result["total"],
        }

    async def get_api_analytics(self):
        data = await self.repo.get_api_analytics()
        return {
            "daily_hits": data["daily_hits"] or 0,
            "top_routes": [
                {
                    "method": row.method,
                    "endpoint": row.endpoint,
                    "total_hits": row.total_hits,
                    "avg_duration": float(row.avg_duration_ms),
                }
                for row in data["top_routes"]
            ],
            "weekly_hits": [{"date": str(row.date_hit), "hits": row.hits} for row in data["weekly_data"]],
        }

    async def get_recent_activity(self, limit: int = 10):
        concepts, users = await asyncio.gather(
            self.repo.get_recent_activity_concepts(limit), self.repo.get_recent_activity_users(limit)
        )

        activity = []
        for c in concepts:
            if c.date_modification:
                activity.append(
                    {"id": c.id, "nom": c.nom, "type": "concept", "action": "creation", "date": c.date_modification}
                )

        for u in users:
            if u.created_at:
                activity.append(
                    {"id": u.id, "nom": u.username, "type": "user", "action": "creation", "date": u.created_at}
                )

        def get_timestamp(item: dict) -> float:
            d = item.get("date")
            if isinstance(d, datetime):
                return d.timestamp()
            return 0.0

        activity.sort(key=get_timestamp, reverse=True)
        return activity[:limit]
