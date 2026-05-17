import httpx
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_get_type_success(async_client: httpx.AsyncClient, setup_test_type):
    type_id = setup_test_type["id"]
    response = await async_client.get(f"/type/{type_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["id"] == type_id
    assert response_data["data"]["type"] == setup_test_type["type"]


@pytest.mark.asyncio
async def test_get_type_no_type(async_client: httpx.AsyncClient):
    type_id = 9999
    response = await async_client.get(f"/type/{type_id}")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "Type introuvable" in response_data["error"]


@pytest.mark.asyncio
async def test_update_type(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = setup_test_type["id"]
    payload = {
        "value": "new_type",
        "field": "type"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] is None

    result = await db_session.execute(text("SELECT type FROM type WHERE id = :id"), {"id": type_id})
    await db_session.commit()
    db_type = result.mappings().first()
    assert db_type["type"] == "new_type"


@pytest.mark.asyncio
async def test_update_type_no_type(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = 9999
    payload = {
        "value": "new_type",
        "field": "type"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Type introuvable" in data["error"]


@pytest.mark.asyncio
async def test_wrong_field_update_type(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = setup_test_type["id"]
    payload = {
        "value": "new_type",
        "field": "wrong_field"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "pas autorisé pour une mise à jour" in data["error"]


@pytest.mark.asyncio
async def test_get_all_types(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type):
    response = await async_client.get("/type/")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data
    data = response_data["data"]
    assert len(data) == 1
    assert data[0]["id"] == setup_test_type["id"]
    assert data[0]["type"] == setup_test_type["type"]


@pytest.mark.asyncio
async def test_create_type(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value": "new_type"
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data

    result = await db_session.execute(text("SELECT id, type FROM type WHERE type = :type"), {"type": payload["value"]})
    await db_session.commit()
    db_type = result.mappings().first()
    assert db_type["type"] == payload["value"]
    assert db_type["id"] is not None


@pytest.mark.asyncio
async def test_create_type_empty(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value": ""
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["success"] is False
    assert "error" in response_data
    assert "Type vide" in response_data["error"]


@pytest.mark.asyncio
async def test_create_type_conflict(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value": setup_test_type["type"]
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_type_by_name(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type):
    response = await async_client.get(f"/type/name/{setup_test_type['type']}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data
    data = response_data["data"]
    assert data["id"] == setup_test_type["id"]
    assert data["type"] == setup_test_type["type"]


@pytest.mark.asyncio
async def test_get_type_by_name_not_found(db_session: AsyncSession, async_client: httpx.AsyncClient, setup_test_type):
    response = await async_client.get(f"/type/name/wrong_name")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "Type introuvable" in response_data["error"]