from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.db.models import Comment, User, Concept


class CommentsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_comments_by_concept(self, concept_id: int):
        query = (
            select(Comment)
            .where(Comment.concept_id == concept_id, Comment.is_deleted.is_(False))
            .options(selectinload(Comment.user))
            .order_by(Comment.created_at.asc())
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_id_by_username(self, username: str):
        query = select(User.id).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_concept_by_id(self, concept_id: int):
        return await self.db.get(Concept, concept_id)

    async def get_comment_by_id(self, comment_id: int):
        return await self.db.get(Comment, comment_id)

    async def add_comment(self, comment: Comment):
        self.db.add(comment)
        await self.db.flush()
        return comment

    async def flush(self):
        await self.db.flush()

    async def refresh(self, obj):
        await self.db.refresh(obj)

    async def get_recent_comments(self, limit: int):
        query = (
            select(Comment)
            .where(Comment.is_deleted.is_(False))
            .options(selectinload(Comment.user), selectinload(Comment.concept))
            .order_by(desc(Comment.created_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
