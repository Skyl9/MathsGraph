import pytest
from httpx import AsyncClient
from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_get_user_success(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    username = setup_test_user["username"]
    response = await async_client.get(f"/users/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["username"] == username


@pytest.mark.asyncio
async def test_get_user_fail(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/users/{user_id}", headers=headers)
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]


@pytest.mark.asyncio
async def test_get_user_by_username(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    username = setup_test_user["username"]
    response = await async_client.get(f"/users/id/{username}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["id"] == str(setup_test_user["id"])


@pytest.mark.asyncio
async def test_get_user_by_username_fail(async_client: AsyncClient, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    username = "fake_user"
    response = await async_client.get(f"/users/id/{username}", headers=headers)
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]


@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    payload = {"field": "email", "value": "test.r@gmail.com"}
    response = await async_client.patch(f"/users/{user_id}", json=payload, headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True


@pytest.mark.asyncio
async def test_update_user_wrong_field(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    payload = {"field": "WrongField", "value": "test.r@gmail.com"}
    response = await async_client.patch(f"/users/{user_id}", json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Mauvais champ donné" in data["error"]


@pytest.mark.asyncio
async def test_update_user_not_found(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = "00000000-0000-0000-0000-000000000000"
    payload = {"field": "email", "value": "test.r@gmail.com"}
    response = await async_client.patch(f"/users/{user_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]


@pytest.mark.asyncio
async def test_get_user_favs_void(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    response = await async_client.get(f"/users/favorite/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] == []


@pytest.mark.asyncio
async def test_get_user_favs_with_data(
    async_client: AsyncClient, setup_test_user, setup_fav_user, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    response = await async_client.get(f"/users/favorite/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] != []


@pytest.mark.asyncio
async def test_get_user_favs_with_wrong_user(
    async_client: AsyncClient, setup_test_user, setup_fav_user, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = "00000000-0000-0000-0000-000000000000"
    response = await async_client.get(f"/users/favorite/{user_id}", headers=headers)
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]


@pytest.mark.asyncio
async def test_delete_user_fav(async_client: AsyncClient, setup_test_user, setup_fav_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    concept_id = setup_fav_user["concept_id"]
    payload = {"type": "concept", "user_id": str(user_id)}
    response = await async_client.request("DELETE", f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_user_fav_forbidden(async_client: AsyncClient, setup_test_user, setup_fav_user):
    # Appeler avec un token utilisateur lambda (pas admin) pour un autre utilisateur
    from fastapi import Response
    from tests.constants import TEST_PASSWORD, TEST_USER_NAME

    # login with standard user
    login_data = {"username": TEST_USER_NAME, "password": TEST_PASSWORD}
    _ = Response()

    # We need db_session, let's just make a POST to /token
    response_login = await async_client.post("/token", data=login_data)
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    concept_id = setup_fav_user["concept_id"]
    payload = {
        "type": "concept",
        "user_id": "00000000-0000-0000-0000-000000000000",  # Not the caller id!
    }
    response = await async_client.request("DELETE", f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "Not authorized to modify this user's favorites" in data["error"]


@pytest.mark.asyncio
async def test_delete_user_fav_wrong_user(
    async_client: AsyncClient, setup_test_concept, setup_test_user, setup_fav_user, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = "00000000-0000-0000-0000-000000000000"
    concept_id = setup_fav_user["id"]
    payload = {"type": "concept", "user_id": str(user_id)}
    response = await async_client.request("DELETE", f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]


@pytest.mark.asyncio
async def test_delete_user_fav_wrong_concept(
    async_client: AsyncClient, setup_test_concept, setup_test_user, setup_fav_user, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    concept_id = setup_fav_user["id"] + 1
    payload = {"type": "concept", "user_id": str(user_id)}
    response = await async_client.request("DELETE", f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept not found" in data["error"]


@pytest.mark.asyncio
async def test_add_user_fav(async_client: AsyncClient, setup_test_user, setup_test_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    concept_id = setup_test_concept["id"]
    payload = {"user_id": str(user_id), "type": "concept"}
    response = await async_client.post(f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_add_user_fav_forbidden(async_client: AsyncClient, setup_test_user, setup_test_concept):
    from tests.constants import TEST_PASSWORD, TEST_USER_NAME

    # login with standard user
    login_data = {"username": TEST_USER_NAME, "password": TEST_PASSWORD}
    response_login = await async_client.post("/token", data=login_data)
    token = response_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    concept_id = setup_test_concept["id"]
    payload = {
        "user_id": "00000000-0000-0000-0000-000000000000",  # Not the caller id!
        "type": "concept",
    }
    response = await async_client.post(f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "Not authorized to modify this user's favorites" in data["error"]


@pytest.mark.asyncio
async def test_add_user_fav_no_concept(
    async_client: AsyncClient, setup_test_user, setup_test_concept, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    concept_id = setup_test_concept["id"] + 1
    payload = {"user_id": str(user_id), "type": "concept"}
    response = await async_client.post(f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept not found" in data["error"]


@pytest.mark.asyncio
async def test_add_user_fav_no_user(
    async_client: AsyncClient, setup_test_user, setup_test_concept, setup_user_token_admin
):
    headers = create_headers_token(setup_user_token_admin)
    user_id = "00000000-0000-0000-0000-000000000000"
    concept_id = setup_test_concept["id"]
    payload = {"user_id": str(user_id), "type": "concept"}
    response = await async_client.post(f"/users/favorite/{concept_id}", json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]


@pytest.mark.asyncio
async def test_get_user_history(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    user_id = setup_test_user["id"]
    response = await async_client.get(f"/users/history/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert isinstance(response_data["data"], list)
