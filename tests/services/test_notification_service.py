import pytest
from app.services.notification_service import NotificationService
from app.core.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_notification(db_session: AsyncSession, setup_test_user, setup_test_concept):
    user_id = setup_test_user["id"]
    concept_id = setup_test_concept["id"]
    service = NotificationService(db_session)

    notif = await service.create_notification(user_id=user_id, message="Test message", concept_id=concept_id)

    assert notif.id is not None
    assert notif.user_id == user_id
    assert notif.message == "Test message"
    assert notif.concept_id == concept_id
    assert notif.is_read is False


@pytest.mark.asyncio
async def test_get_unread_notifications(db_session: AsyncSession, setup_test_user):
    user_id = setup_test_user["id"]
    service = NotificationService(db_session)

    await service.create_notification(user_id=user_id, message="Test 1")
    await service.create_notification(user_id=user_id, message="Test 2")

    unread = await service.get_unread_notifications(user_id)
    assert len(unread) == 2


@pytest.mark.asyncio
async def test_mark_as_read(db_session: AsyncSession, setup_test_user):
    user_id = setup_test_user["id"]
    service = NotificationService(db_session)

    notif = await service.create_notification(user_id=user_id, message="Test 1")
    assert notif.is_read is False

    read_notif = await service.mark_as_read(notif.id)
    assert read_notif.is_read is True
    assert read_notif.id == notif.id

    unread = await service.get_unread_notifications(user_id)
    assert len(unread) == 0


@pytest.mark.asyncio
async def test_mark_as_read_not_found(db_session: AsyncSession):
    service = NotificationService(db_session)
    with pytest.raises(NotFoundException) as exc_info:
        await service.mark_as_read(9999)
    assert "introuvable" in exc_info.value.detail


@pytest.mark.asyncio
async def test_mark_all_as_read(db_session: AsyncSession, setup_test_user):
    user_id = setup_test_user["id"]
    service = NotificationService(db_session)

    await service.create_notification(user_id=user_id, message="Test 1")
    await service.create_notification(user_id=user_id, message="Test 2")

    await service.mark_all_as_read(user_id)

    unread = await service.get_unread_notifications(user_id)
    assert len(unread) == 0
