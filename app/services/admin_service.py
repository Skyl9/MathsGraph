import logging
from datetime import date, timedelta, datetime
from sqlalchemy import select, func, desc, cast, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User, UserFavorite, Concept, Category, Mathematicien, ApiLog

logger = logging.getLogger(__name__)


class AdminService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self):
        # Utilisation de requêtes scalaires pour compter les entrées dans chaque table
        users_count = await self.db.scalar(select(func.count()).select_from(User))
        favorites_count = await self.db.scalar(select(func.count()).select_from(UserFavorite))
        concepts_count = await self.db.scalar(select(func.count()).select_from(Concept))
        categories_count = await self.db.scalar(select(func.count()).select_from(Category))
        mathematicien_count = await self.db.scalar(select(func.count()).select_from(Mathematicien))

        thirty_days_ago = date.today() - timedelta(days=30)
        users_growth = await self.db.scalar(
            select(func.count()).select_from(User).where(User.created_at >= thirty_days_ago)
        )
        concepts_growth = await self.db.scalar(
            select(func.count()).select_from(Concept).where(Concept.date_modification >= thirty_days_ago)
        )

        return {
            "users": users_count or 0,
            "favorites": favorites_count or 0,
            "concepts": concepts_count or 0,
            "categories": categories_count or 0,
            "mathematicien": mathematicien_count or 0,
            "users_growth": users_growth or 0,
            "concepts_growth": concepts_growth or 0,
        }

    async def get_users(self, skip: int = 0, limit: int = 50):
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        users = result.scalars().all()

        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at,
            }
            for u in users
        ]

    async def get_concepts_admin(self, skip: int = 0, limit: int = 50):
        query = select(Concept).options(selectinload(Concept.type)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        concepts = result.scalars().all()

        return [
            {
                "id": c.id,
                "nom": c.nom,
                "type": c.type.type if c.type else None,
            }
            for c in concepts
        ]

    async def get_api_analytics(self):
        # Top 10 des routes les plus appelées
        # SELECT method, endpoint, COUNT(*), ROUND(AVG(duration_ms)::numeric, 2)
        query_top = (
            select(
                ApiLog.method,
                ApiLog.endpoint,
                func.count().label("total_hits"),
                func.round(cast(func.avg(ApiLog.duration_ms), Numeric), 2).label("avg_duration_ms"),
            )
            .group_by(ApiLog.method, ApiLog.endpoint)
            .order_by(desc("total_hits"))
            .limit(10)
        )
        result_top = await self.db.execute(query_top)
        top_routes = result_top.all()

        # Nombre total de requêtes aujourd'hui
        today = date.today()
        query_daily = select(func.count()).where(func.date(ApiLog.created_at) == today)
        daily_hits = await self.db.scalar(query_daily)

        seven_days_ago = today - timedelta(days=7)
        query_weekly = (
            select(func.date(ApiLog.created_at).label("date_hit"), func.count().label("hits"))
            .where(ApiLog.created_at >= seven_days_ago)
            .group_by(func.date(ApiLog.created_at))
            .order_by(func.date(ApiLog.created_at))
        )
        result_weekly = await self.db.execute(query_weekly)
        weekly_data = result_weekly.all()

        return {
            "daily_hits": daily_hits or 0,
            "top_routes": [
                {
                    "method": row.method,
                    "endpoint": row.endpoint,
                    "total_hits": row.total_hits,
                    "avg_duration": float(row.avg_duration_ms),
                }
                for row in top_routes
            ],
            "weekly_hits": [{"date": str(row.date_hit), "hits": row.hits} for row in weekly_data],
        }

    async def get_recent_activity(self, limit: int = 10):
        # Fetch latest concepts
        query_concepts = select(Concept).order_by(desc(Concept.date_modification)).limit(limit)
        concepts = (await self.db.execute(query_concepts)).scalars().all()

        # Fetch latest users
        query_users = select(User).order_by(desc(User.created_at)).limit(limit)
        users = (await self.db.execute(query_users)).scalars().all()

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

        # Sort by date descending, robustly handling None and mix of naive/aware datetimes
        def get_timestamp(item: dict) -> float:
            d = item.get("date")
            if isinstance(d, datetime):
                return d.timestamp()
            return 0.0

        activity.sort(key=get_timestamp, reverse=True)
        return activity[:limit]
