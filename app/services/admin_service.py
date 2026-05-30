import logging
from datetime import date
from sqlalchemy import select, func, text, desc, cast, Numeric
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import User, UserFavorite, Concept, Category, Mathematicien, Type, ApiLog

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

        return {
            "users": users_count,
            "favorites": favorites_count,
            "concepts": concepts_count,
            "categories": categories_count,
            "mathematicien": mathematicien_count,
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
                func.round(cast(func.avg(ApiLog.duration_ms), Numeric), 2).label("avg_duration_ms")
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

        return {
            "daily_hits": daily_hits or 0,
            "top_routes": [
                {
                    "method": row.method,
                    "endpoint": row.endpoint,
                    "total_hits": row.total_hits,
                    "avg_duration": float(row.avg_duration_ms)
                } for row in top_routes
            ]
        }
