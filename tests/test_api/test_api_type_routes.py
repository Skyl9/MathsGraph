import psycopg.rows
import pytest
import httpx
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
async def test_update_type(transaction,async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = setup_test_type["id"]
    payload={
        "value":"new_type",
        "field":"type"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] is None
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("SELECT type FROM type WHERE id = %s;", (type_id,))
        db_type = await cur.fetchone()
        assert db_type["type"] == "new_type"

@pytest.mark.asyncio
async def test_update_type_no_type(transaction,async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = 9999
    payload={
        "value":"new_type",
        "field":"type"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Type introuvable" in data["error"]

@pytest.mark.asyncio
async def test_wrong_field_update_type(transaction,async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    type_id = setup_test_type["id"]
    payload={
        "value":"new_type",
        "field":"wrong_field"
    }
    response = await async_client.patch(f"/type/{type_id}", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "error" in data
    assert "pas autorisé pour une mise à jour" in data["error"]


@pytest.mark.asyncio
async def test_get_all_types(transaction,async_client: httpx.AsyncClient, setup_test_type):
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
async def test_create_type(transaction,async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value":"new_type"
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data
    data = response_data["data"]

    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("SELECT id, type FROM type WHERE type = %s;", (payload["value"],))
        db_type = await cur.fetchone()
        assert db_type["type"] == payload["value"]
        assert db_type["id"] is not None

@pytest.mark.asyncio
async def test_create_type_empty(transaction,async_client: httpx.AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value":""
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 400
    response_data = response.json()
    assert response_data["success"] is False
    assert "error" in response_data
    assert "Type vide" in response_data["error"]

@pytest.mark.asyncio
async def test_create_type_conflict(transaction,async_client: httpx.AsyncClient, setup_test_type, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "value":setup_test_type["type"]
    }
    response = await async_client.post("/type", json=payload, headers=headers)
    assert response.status_code == 409

@pytest.mark.asyncio
async def test_get_type_by_name(transaction,async_client: httpx.AsyncClient, setup_test_type):

    response = await async_client.get(f"/type/name/{setup_test_type["type"]}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert "data" in response_data
    data = response_data["data"]
    assert data["id"] == setup_test_type["id"]
    assert data["type"] == setup_test_type["type"]

@pytest.mark.asyncio
async def test_get_type_by_name_not_found(transaction,async_client: httpx.AsyncClient, setup_test_type):
    response = await async_client.get(f"/type/name/wrong_name")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "Type introuvable" in response_data["error"]
