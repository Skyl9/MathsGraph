from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, cast, Numeric
from sqlalchemy.orm import selectinload
from datetime import date, timedelta
from app.db.models import User, UserFavorite, Concept, Category, Mathematicien, ApiLog


class AdminRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_stats(self):
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

    async def get_users(self, skip: int, limit: int):
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_concepts_admin(self, skip: int, limit: int):
        query = select(Concept).options(selectinload(Concept.type)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_api_analytics(self):
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

        return {"top_routes": top_routes, "daily_hits": daily_hits, "weekly_data": weekly_data}

    async def get_recent_activity_concepts(self, limit: int):
        query_concepts = select(Concept).order_by(desc(Concept.date_modification)).limit(limit)
        return (await self.db.execute(query_concepts)).scalars().all()

    async def get_recent_activity_users(self, limit: int):
        query_users = select(User).order_by(desc(User.created_at)).limit(limit)
        return (await self.db.execute(query_users)).scalars().all()
