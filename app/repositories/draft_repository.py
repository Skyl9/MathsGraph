from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID as PyUUID
from app.db.models import ConceptDraft


class DraftRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_drafts_by_user(self, user_id: PyUUID):
        stmt = select(ConceptDraft).where(ConceptDraft.user_id == user_id).order_by(ConceptDraft.updated_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_draft_by_id(self, draft_id: int):
        stmt = select(ConceptDraft).where(ConceptDraft.id == draft_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_draft(self, user_id: PyUUID, concept_id: int | None, draft_data: dict):
        draft = ConceptDraft(user_id=user_id, concept_id=concept_id, draft_data=draft_data)
        self.db.add(draft)
        await self.db.commit()
        await self.db.refresh(draft)
        return draft

    async def update_draft(self, draft_id: int, draft_data: dict):
        stmt = (
            update(ConceptDraft)
            .where(ConceptDraft.id == draft_id)
            .values(draft_data=draft_data)
            .returning(ConceptDraft)
        )
        result = await self.db.execute(stmt)
        draft = result.scalar_one_or_none()
        if draft:
            await self.db.commit()
            await self.db.refresh(draft)
        return draft

    async def delete_draft(self, draft_id: int):
        draft = await self.get_draft_by_id(draft_id)
        if draft:
            await self.db.delete(draft)
            await self.db.commit()
            return True
        return False
