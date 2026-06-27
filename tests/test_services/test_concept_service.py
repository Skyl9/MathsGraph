import pytest
from unittest.mock import AsyncMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.concept_service import ConceptService
from app.schemas.concept import ConceptCreate, RollbackConcept
from app.schemas import UpdateConceptDict
from app.core.exceptions import NotFoundException, ConflictException


@pytest.mark.asyncio
async def test_get_concept_info_success(db_session: AsyncSession, setup_full_test_concept):
    service = ConceptService(db_session)
    concept_id = setup_full_test_concept["concept"]["id"]
    result = await service.get_concept_info(concept_id)
    assert result["id"] == concept_id
    assert result["nom"] == setup_full_test_concept["concept"]["nom"]
    assert len(result["aliases"]) == 2
    assert len(result["sources"]) == 1
    assert len(result["relations"]) == 1


@pytest.mark.asyncio
async def test_get_concept_info_not_found(db_session: AsyncSession):
    service = ConceptService(db_session)
    with pytest.raises(NotFoundException, match="Concept non trouvé"):
        await service.get_concept_info(999999)


@pytest.mark.asyncio
@patch("app.services.concept_service.invalidate_graph_cache", new_callable=AsyncMock)
@patch("app.services.concept_service.redis_db.delete", new_callable=AsyncMock)
async def test_create_concept_success(
    mock_redis_delete, mock_invalidate, db_session: AsyncSession, setup_test_user, setup_test_type
):
    service = ConceptService(db_session)
    data = ConceptCreate(
        nom="Nouveau Concept", enonce="Ceci est un énoncé", demonstration="Une démo", type=setup_test_type["type"]
    )
    result = await service.create_concept(data, setup_test_user["username"])
    assert result["nom"] == "Nouveau Concept"
    assert "id" in result
    mock_invalidate.assert_called_once()


@pytest.mark.asyncio
async def test_create_concept_conflict(db_session: AsyncSession, setup_test_concept, setup_test_user):
    service = ConceptService(db_session)
    data = ConceptCreate(nom=setup_test_concept["nom"], enonce="Ceci est un énoncé")
    with pytest.raises(ConflictException, match="Un concept avec ce nom existe déjà."):
        await service.create_concept(data, setup_test_user["username"])


@pytest.mark.asyncio
@patch("app.services.concept_service.invalidate_graph_cache", new_callable=AsyncMock)
@patch("app.services.concept_service.redis_db.delete", new_callable=AsyncMock)
async def test_update_concept_success(
    mock_redis_delete, mock_invalidate, db_session: AsyncSession, setup_test_concept, setup_test_user
):
    service = ConceptService(db_session)
    update_data = UpdateConceptDict(field="enonce", value="Nouvel énoncé test", username=setup_test_user["username"])
    await service.updateConcept(setup_test_concept["id"], update_data)

    info = await service.get_concept_info(setup_test_concept["id"])
    assert info["enonce"] == "Nouvel énoncé test"
    mock_invalidate.assert_called_once()
    mock_redis_delete.assert_called_once()


@pytest.mark.asyncio
async def test_update_concept_not_found(db_session: AsyncSession, setup_test_user):
    service = ConceptService(db_session)
    update_data = UpdateConceptDict(field="enonce", value="Nouvel énoncé test", username=setup_test_user["username"])
    with pytest.raises(NotFoundException, match="Concept non trouvé"):
        await service.updateConcept(999999, update_data)


@pytest.mark.asyncio
@patch("app.services.concept_service.invalidate_graph_cache", new_callable=AsyncMock)
@patch("app.services.concept_service.redis_db.delete", new_callable=AsyncMock)
async def test_rollback_history_success(
    mock_redis_delete, mock_invalidate, db_session: AsyncSession, setup_test_concept, setup_test_user
):
    service = ConceptService(db_session)

    # Update first to create a history version
    update_data = UpdateConceptDict(field="enonce", value="Modifié", username=setup_test_user["username"])
    await service.updateConcept(setup_test_concept["id"], update_data)

    history = await service.get_concept_versions(setup_test_concept["id"])
    assert len(history) > 0
    target_version = next((v for v in history if v.field_modified == "enonce" and v.new_value == "Modifié"), None)
    assert target_version is not None

    rollback_data = RollbackConcept(
        version_number=target_version.version_number,
        field_modified=target_version.field_modified,
        username=setup_test_user["username"],
    )

    await service.rollback_history(setup_test_concept["id"], rollback_data)

    info = await service.get_concept_info(setup_test_concept["id"])
    assert info["enonce"] == target_version.old_value


@pytest.mark.asyncio
async def test_rollback_history_not_found(db_session: AsyncSession, setup_test_user):
    service = ConceptService(db_session)
    rollback_data = RollbackConcept(version_number=999, field_modified="enonce", username=setup_test_user["username"])
    with pytest.raises(NotFoundException, match="Version non trouvée"):
        await service.rollback_history(999999, rollback_data)
