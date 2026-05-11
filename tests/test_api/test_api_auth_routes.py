import pytest
from psycopg import rows

from tests.constants import TEST_USER_EMAIL, TEST_PASSWORD, TEST_USER_NAME


@pytest.mark.asyncio
async def test_register(async_client, transaction):
    user_data = {
        "email": TEST_USER_EMAIL,
        "password": TEST_PASSWORD,
        "username": TEST_USER_NAME
    }
    response = await async_client.post("/register", json=user_data)
    responseA = response.json()
    print(responseA)
    body = responseA["data"]
    assert response.status_code == 200, "L'utilisateur a bien pu s'inscrire !"

    assert body["email"] == user_data["email"]
    assert body["username"] == user_data["username"]

    # Vérifier que l'utilisateur est bien dans la base
    async with transaction.cursor(row_factory=rows.dict_row) as cur:
        await cur.execute("SELECT * FROM users WHERE email=%s", (TEST_USER_EMAIL,))
        user_in_db = await cur.fetchone()
        assert user_in_db is not None
        assert user_in_db["email"] == user_data["email"]


@pytest.mark.asyncio
async def test_login(async_client, setup_test_user):
    login_data = {
        "username": TEST_USER_NAME,
        "password": TEST_PASSWORD
    }
    response = await async_client.post("/token", data=login_data)

    assert response.status_code == 200, "Connexion réussie"
    response_body = response.json()
    assert "access_token" in response_body["data"]
    assert response_body["data"]["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_request_password_token(transaction,async_client, setup_test_user,):
    login_data = {
        "email": TEST_USER_EMAIL,
    }
    response = await async_client.post("/password-reset/request", json=login_data)
    assert response.status_code == 200
    response = response.json()
    data = response["data"]
    assert response["success"] == True
    assert type(data) == dict
    async with transaction.cursor() as cur:
        await cur.execute("SELECT id FROM users WHERE email = %s", (TEST_USER_EMAIL,))
        user_id = await cur.fetchone()
        assert user_id is not None
        await cur.execute("SELECT token FROM password_reset_tokens WHERE user_id = %s", (user_id[0],))
        token = await cur.fetchone()
        assert token is not None

@pytest.mark.asyncio
async def test_reset_password(transaction,async_client, setup_reset_token,setup_test_user,):

    login_data = {
        "token": setup_reset_token["token"],
        "new_password":"testtest"
    }
    response = await async_client.post("/password-reset/confirm", json=login_data)
    assert response.status_code == 200
    response = response.json()
    msg = response["data"]
    assert response["success"] == True


