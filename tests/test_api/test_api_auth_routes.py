from unittest.mock import patch, AsyncMock
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, PasswordResetToken
from tests.constants import TEST_USER_EMAIL, TEST_PASSWORD, TEST_USER_NAME


@pytest.mark.asyncio
async def test_register(async_client: pytest.fixture, db_session: AsyncSession):
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USER_NAME
    }
    response = await async_client.post("/register", json=user_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    body = response_data["data"]

    assert body["email"] == user_data["email"]
    assert body["username"] == user_data["username"]

    # Vérifier que l'utilisateur est bien dans la base via SQLAlchemy
    query = select(User).where(User.email == TEST_USER_EMAIL)
    result = await db_session.execute(query)
    user_in_db = result.scalars().first()
    assert user_in_db is not None
    assert user_in_db.email == user_data["email"]


@pytest.mark.asyncio
async def test_login(async_client, setup_test_user):
    login_data = {
        "username": TEST_USER_NAME,
        "password": TEST_PASSWORD
    }
    response = await async_client.post("/token", data=login_data)

    assert response.status_code == 200, "Connexion réussie"
    response_body = response.json()
    assert "access_token" in response_body
    assert response_body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_reset_password(async_client, db_session: AsyncSession, setup_reset_token, setup_test_user):
    login_data = {
        "token": setup_reset_token["token"],
        "new_password": "newpassword123"
    }
    response = await async_client.post("/password-reset/confirm", json=login_data)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

    # Vérifier que le mot de passe a été mis à jour (via le login par exemple, ou en vérifiant le hash)
    # Ici on fait simple: on vérifie que le token a été marqué comme utilisé
    query = select(PasswordResetToken).where(PasswordResetToken.token == setup_reset_token["token"])
    result = await db_session.execute(query)
    token_db = result.scalars().first()
    assert token_db is not None
    assert token_db.used is True


@pytest.mark.asyncio
@patch("app.services.auth_service.aiosmtplib.send", new_callable=AsyncMock)
async def test_request_password_token(mock_send, async_client, db_session: AsyncSession, setup_test_user):
    login_data = {
        "email": TEST_USER_EMAIL,
    }

    response = await async_client.post("/password-reset/request", json=login_data)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

    # Vérifier le token en DB
    query_user = select(User).where(User.email == TEST_USER_EMAIL)
    res_user = await db_session.execute(query_user)
    user = res_user.scalars().first()
    assert user is not None

    query_token = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    res_token = await db_session.execute(query_token)
    token = res_token.scalars().first()
    assert token is not None

    # Vérifier que aiosmtplib.send a été appelé une fois
    assert mock_send.called
