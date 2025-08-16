import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_user_success(async_client: AsyncClient, setup_test_user):
    user_id = setup_test_user["id"]
    username = setup_test_user["username"]
    response = await async_client.get(f"/user/{user_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["username"] == username


@pytest.mark.asyncio
async def test_get_user_fail(async_client: AsyncClient, setup_test_user):
    user_id = 99999
    response = await async_client.get(f"/user/{user_id}")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]

@pytest.mark.asyncio
async def test_get_user_by_username(async_client: AsyncClient, setup_test_user):
    username = setup_test_user["username"]
    response = await async_client.get(f"/user/id/{username}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"]["id"] == setup_test_user["id"]

@pytest.mark.asyncio
async def test_get_user_by_username_fail(async_client: AsyncClient):
    username = "fake_user"
    response = await async_client.get(f"/user/id/{username}")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]

@pytest.mark.asyncio
async def test_update_user(async_client: AsyncClient, setup_test_user):
    user_id = setup_test_user["id"]
    payload={
        "field":"email",
        "value":"test.r@gmail.com"
    }
    response = await async_client.patch(f"/user/update/{user_id}", json=payload)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True

@pytest.mark.asyncio
async def test_update_user_wrong_field(async_client: AsyncClient, setup_test_user):
    user_id = setup_test_user["id"]
    payload={
        "field":"WrongField",
        "value":"test.r@gmail.com"
    }
    response = await async_client.patch(f"/user/update/{user_id}", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Mauvais champ donné" in data["error"]

@pytest.mark.asyncio
async def test_update_user_wrong_field(async_client: AsyncClient, setup_test_user):
    user_id = setup_test_user["id"]+1
    payload={
        "field":"email",
        "value":"test.r@gmail.com"
    }
    response = await async_client.patch(f"/user/update/{user_id}", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]

@pytest.mark.asyncio
async def test_get_user_favs_void(async_client: AsyncClient, setup_test_user):
    user_id = setup_test_user["id"]
    response = await async_client.get(f"/user/favorite/{user_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] == []

@pytest.mark.asyncio
async def test_get_user_favs_with_data(async_client: AsyncClient,transaction, setup_test_user, setup_fav_user):
    user_id = setup_test_user["id"]
    response = await async_client.get(f"/user/favorite/{user_id}")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["success"] is True
    assert response_data["data"] != []

@pytest.mark.asyncio
async def test_get_user_favs_with_wrong_user(async_client: AsyncClient,transaction, setup_test_user, setup_fav_user):
    user_id = setup_test_user["id"]+1
    response = await async_client.get(f"/user/favorite/{user_id}")
    assert response.status_code == 404
    response_data = response.json()
    assert response_data["success"] is False
    assert "User not found" in response_data["error"]
@pytest.mark.asyncio
async def test_delete_user_fav(async_client: AsyncClient,transaction, setup_test_user, setup_fav_user):
    user_id = setup_test_user["id"]
    concept_id = setup_fav_user["id"]
    payload = {
        "type":"concept",
        "user_id":str(user_id)
    }
    response = await async_client.request("DELETE",f"/user/favorite/delete/{concept_id}", json=payload)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_delete_user_fav_wrong_user(async_client: AsyncClient,transaction,setup_test_concept, setup_test_user, setup_fav_user):
    user_id = setup_test_user["id"]+1
    concept_id = setup_fav_user["id"]
    payload = {
        "type":"concept",
        "user_id":str(user_id)
    }
    response = await async_client.request("DELETE",f"/user/favorite/delete/{concept_id}", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]

@pytest.mark.asyncio
async def test_delete_user_fav_wrong_concept(async_client: AsyncClient,transaction,setup_test_concept, setup_test_user, setup_fav_user):
    user_id = setup_test_user["id"]
    concept_id = setup_fav_user["id"]+1
    payload = {
        "type":"concept",
        "user_id":str(user_id)
    }
    response = await async_client.request("DELETE",f"/user/favorite/delete/{concept_id}", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept not found" in data["error"]

@pytest.mark.asyncio
async def test_add_user_fav(async_client: AsyncClient,transaction, setup_test_user, setup_test_concept):
    user_id = setup_test_user["id"]
    concept_id = setup_test_concept["id"]
    payload ={
        "user_id":str(user_id),
        "type":"concept"
    }
    response = await async_client.post(f"/user/favorite/add/{concept_id}", json=payload)
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_add_user_fav_no_concept(async_client: AsyncClient,transaction, setup_test_user, setup_test_concept):
    user_id = setup_test_user["id"]
    concept_id = setup_test_concept["id"]+1
    payload ={
        "user_id":str(user_id),
        "type":"concept"
    }
    response = await async_client.post(f"/user/favorite/add/{concept_id}", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept not found" in data["error"]

@pytest.mark.asyncio
async def test_add_user_fav_no_user(async_client: AsyncClient,transaction, setup_test_user, setup_test_concept):
    user_id = setup_test_user["id"]+1
    concept_id = setup_test_concept["id"]
    payload ={
        "user_id":str(user_id),
        "type":"concept"
    }
    response = await async_client.post(f"/user/favorite/add/{concept_id}", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["error"]

