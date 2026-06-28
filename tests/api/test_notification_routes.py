import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.db.models import User
from app.services.notification_service import NotificationService
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_get_notifications(async_client: AsyncClient, db_session: AsyncSession, setup_user_token_admin):
    token = setup_user_token_admin["access_token"]

    # Récupérer l'utilisateur admin généré par la fixture
    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalars().first()

    service = NotificationService(db_session)
    await service.create_notification(user_id=admin_user.id, message="Admin Notif")

    response = await async_client.get("/notifications", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert len(data["data"]) == 1
    assert data["data"][0]["message"] == "Admin Notif"


@pytest.mark.asyncio
async def test_mark_notification_read(async_client: AsyncClient, db_session: AsyncSession, setup_user_token_admin):
    token = setup_user_token_admin["access_token"]

    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalars().first()

    service = NotificationService(db_session)
    notif = await service.create_notification(user_id=admin_user.id, message="Admin Notif")

    response = await async_client.patch(f"/notifications/{notif.id}/read", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["is_read"] is True

    unread = await service.get_unread_notifications(admin_user.id)
    assert len(unread) == 0


@pytest.mark.asyncio
async def test_mark_all_notifications_read(async_client: AsyncClient, db_session: AsyncSession, setup_user_token_admin):
    token = setup_user_token_admin["access_token"]

    result = await db_session.execute(select(User).where(User.username == "admin"))
    admin_user = result.scalars().first()

    service = NotificationService(db_session)
    await service.create_notification(user_id=admin_user.id, message="Notif 1")
    await service.create_notification(user_id=admin_user.id, message="Notif 2")

    response = await async_client.patch("/notifications/read-all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "marquées comme lues" in data["data"]

    unread = await service.get_unread_notifications(admin_user.id)
    assert len(unread) == 0


@pytest.mark.asyncio
async def test_get_notifications_unauthorized(async_client: AsyncClient):
    response = await async_client.get("/notifications")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"] == "Authentification requise : aucun token trouvé."
