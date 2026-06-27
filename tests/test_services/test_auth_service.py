import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, patch

from fastapi import Response, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.auth_service import AuthService
from app.schemas.auth import UserCreate, PasswordResetConfirmSchema
from app.core.exceptions import ConflictException, AuthenticationException


@pytest.mark.asyncio
async def test_register_user_success(db_session: AsyncSession):
    service = AuthService(db_session)
    user_data = UserCreate(username="newuser_test", email="newuser@example.com", password="password123")
    result = await service.register_user(user_data)
    assert result["username"] == "newuser_test"
    assert result["email"] == "newuser@example.com"
    assert result["is_active"] is True
    assert "id" in result


@pytest.mark.asyncio
async def test_register_user_conflict_username(db_session: AsyncSession, setup_test_user):
    service = AuthService(db_session)
    user_data = UserCreate(username=setup_test_user["username"], email="other@example.com", password="password123")
    with pytest.raises(ConflictException, match="Ce nom d'utilisateur est déjà pris."):
        await service.register_user(user_data)


@pytest.mark.asyncio
async def test_register_user_conflict_email(db_session: AsyncSession, setup_test_user):
    service = AuthService(db_session)
    user_data = UserCreate(username="otheruser", email=setup_test_user["email"], password="password123")
    with pytest.raises(ConflictException, match="Cet email est déjà associé à un compte."):
        await service.register_user(user_data)


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession, setup_test_user):
    from tests.constants import TEST_PASSWORD

    service = AuthService(db_session)
    form = OAuth2PasswordRequestForm(username=setup_test_user["username"], password=TEST_PASSWORD)
    response = Response()
    result = await service.login_for_access_token(form, response)
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    # Verify cookie is set in response headers
    cookies = response.headers.getlist("set-cookie")
    assert any("access_token=" in cookie for cookie in cookies)


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession, setup_test_user):
    service = AuthService(db_session)
    form = OAuth2PasswordRequestForm(username=setup_test_user["username"], password="wrongpassword")
    with pytest.raises(HTTPException) as exc:
        await service.login_for_access_token(form, Response())
    assert exc.value.status_code == 401
    assert exc.value.detail == "Nom d'utilisateur ou mot de passe incorrect"


@pytest.mark.asyncio
@patch("app.services.auth_service.AuthService.send_email", new_callable=AsyncMock)
async def test_request_password_reset_success(mock_send_email, db_session: AsyncSession, setup_test_user):
    service = AuthService(db_session)
    result = await service.request_password_reset(setup_test_user["email"])
    assert result["detail"] == "Un e-mail contenant un lien de réinitialisation de mot de passe a été envoyé."
    mock_send_email.assert_called_once()


@pytest.mark.asyncio
@patch("app.services.auth_service.AuthService.send_email", new_callable=AsyncMock)
async def test_request_password_reset_unknown_email(mock_send_email, db_session: AsyncSession):
    service = AuthService(db_session)
    result = await service.request_password_reset("unknown@example.com")
    assert result["detail"] == "Un e-mail contenant un lien de réinitialisation de mot de passe a été envoyé."
    mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_reset_password_success(db_session: AsyncSession, setup_reset_token):
    service = AuthService(db_session)
    data = PasswordResetConfirmSchema(token=setup_reset_token["token"], new_password="newsecurepassword")
    result = await service.reset_password(data)
    assert result["detail"] == "Mot de passe réinitialisé avec succès"


@pytest.mark.asyncio
async def test_reset_password_too_short(db_session: AsyncSession, setup_reset_token):
    service = AuthService(db_session)
    from pydantic import ValidationError

    with pytest.raises(ValidationError, match="Le mot de passe doit contenir au moins 8 caractères"):
        data = PasswordResetConfirmSchema(token=setup_reset_token["token"], new_password="short")
        await service.reset_password(data)


@pytest.mark.asyncio
async def test_reset_password_invalid_token(db_session: AsyncSession):
    service = AuthService(db_session)
    data = PasswordResetConfirmSchema(token="invalid_token", new_password="newsecurepassword")
    with pytest.raises(AuthenticationException, match="Token invalide"):
        await service.reset_password(data)


@pytest.mark.asyncio
async def test_reset_password_expired_token(db_session: AsyncSession, setup_test_user):
    service = AuthService(db_session)
    import secrets

    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) - timedelta(days=2)

    await db_session.execute(
        text("INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (:user_id, :token, :expires_at)"),
        {"user_id": setup_test_user["id"], "token": reset_token, "expires_at": expires_at},
    )
    await db_session.commit()

    data = PasswordResetConfirmSchema(token=reset_token, new_password="newsecurepassword")
    with pytest.raises(AuthenticationException, match="Token expiré"):
        await service.reset_password(data)
