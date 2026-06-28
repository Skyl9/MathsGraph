from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID as PyUUID
from app.repositories.draft_repository import DraftRepository
from app.services.concept_service import ConceptService
from app.schemas.draft import DraftCreate, DraftUpdate
from app.core.exceptions import NotFoundException, ForbiddenException
from app.schemas.patchClass import UpdateConceptDict
from app.schemas.concept import ConceptCreate


class DraftService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = DraftRepository(db)

    async def get_my_drafts(self, user_id: PyUUID):
        return await self.repo.get_drafts_by_user(user_id)

    async def get_draft(self, draft_id: int, user_id: PyUUID):
        draft = await self.repo.get_draft_by_id(draft_id)
        if not draft:
            raise NotFoundException(detail="Brouillon introuvable")
        if draft.user_id != user_id:
            raise ForbiddenException(detail="Ce brouillon ne vous appartient pas")
        return draft

    async def create_draft(self, user_id: PyUUID, data: DraftCreate):
        return await self.repo.create_draft(user_id, data.concept_id, data.draft_data)

    async def update_draft(self, draft_id: int, user_id: PyUUID, data: DraftUpdate):
        draft = await self.get_draft(draft_id, user_id)
        return await self.repo.update_draft(draft.id, data.draft_data)

    async def publish_draft(self, draft_id: int, user_id: PyUUID, username: str):
        draft = await self.get_draft(draft_id, user_id)
        concept_service = ConceptService(self.db)

        if draft.concept_id:
            # Update existing concept
            for field, value in draft.draft_data.items():
                update_data = UpdateConceptDict(field=field, value=value, username=username)
                await concept_service.updateConcept(draft.concept_id, update_data)
        else:
            # Create new concept
            create_data = ConceptCreate(**draft.draft_data)
            await concept_service.create_concept(create_data, username)

        await self.repo.delete_draft(draft.id)
        return {"message": "Brouillon publié avec succès"}

    async def delete_draft(self, draft_id: int, user_id: PyUUID):
        draft = await self.get_draft(draft_id, user_id)
        await self.repo.delete_draft(draft.id)
