import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.draft_service import DraftService
from app.schemas.draft import DraftCreate, DraftUpdate
from app.core.exceptions import NotFoundException, ForbiddenException
from uuid import uuid4


@pytest.mark.asyncio
async def test_draft_service_crud(db_session: AsyncSession, setup_test_user, setup_test_concept):
    service = DraftService(db_session)
    user_id = setup_test_user["id"]

    # 1. Create
    data = DraftCreate(concept_id=setup_test_concept["id"], draft_data={"nom": "Test Draft"})
    draft = await service.create_draft(user_id, data)
    assert draft.id is not None
    assert draft.draft_data["nom"] == "Test Draft"

    # 2. Get my drafts
    drafts = await service.get_my_drafts(user_id)
    assert len(drafts) == 1
    assert drafts[0].id == draft.id

    # 3. Get specific draft
    fetched = await service.get_draft(draft.id, user_id)
    assert fetched.id == draft.id

    # 4. Update
    updated_data = DraftUpdate(draft_data={"nom": "Updated Draft"})
    updated = await service.update_draft(draft.id, user_id, updated_data)
    assert updated.draft_data["nom"] == "Updated Draft"

    # 5. Delete
    await service.delete_draft(draft.id, user_id)
    drafts_after = await service.get_my_drafts(user_id)
    assert len(drafts_after) == 0


@pytest.mark.asyncio
async def test_draft_service_exceptions(db_session: AsyncSession, setup_test_user, setup_test_concept):
    service = DraftService(db_session)
    user_id = setup_test_user["id"]

    # Not found
    with pytest.raises(NotFoundException):
        await service.get_draft(9999, user_id)

    # Forbidden
    data = DraftCreate(concept_id=setup_test_concept["id"], draft_data={"nom": "Test Draft"})
    draft = await service.create_draft(user_id, data)

    other_user_id = uuid4()
    with pytest.raises(ForbiddenException):
        await service.get_draft(draft.id, other_user_id)
