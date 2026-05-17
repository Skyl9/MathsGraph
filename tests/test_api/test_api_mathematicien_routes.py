import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Mathematicien

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_add_mathematicien_success(async_client: AsyncClient, db_session: AsyncSession, setup_user_token_admin):
    """
    Teste l'ajout d'un nouveau mathématicien via la route POST /mathematicien.
    """
    headers = create_headers_token(setup_user_token_admin)
    test_name = "Ada Lovelace"
    response = await async_client.post("/mathematicien", json={"value": test_name}, headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"] is None
    assert res_data["error"] is None

    # Vérifier que le mathématicien a bien été ajouté à la base de données
    query = select(Mathematicien).where(Mathematicien.nom == test_name)
    result = await db_session.execute(query)
    added_mathematicien = result.scalars().first()
    assert added_mathematicien is not None
    assert added_mathematicien.nom == test_name


@pytest.mark.asyncio
async def test_get_one_mathematicien_success(async_client: AsyncClient, setup_test_mathematicien: dict):
    """
    Teste la récupération d'un mathématicien par ID via la route GET /mathematicien/{id_mathematicien}.
    """
    mathematicien_id = setup_test_mathematicien["id"]
    expected_name = setup_test_mathematicien["nom"]

    response = await async_client.get(f"/mathematicien/{mathematicien_id}")

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["error"] is None
    assert res_data["data"] is not None

    data = res_data["data"]
    assert data["id"] == mathematicien_id
    assert data["nom"] == expected_name


@pytest.mark.asyncio
async def test_get_one_mathematicien_not_found(async_client: AsyncClient):
    """
    Teste la récupération d'un mathématicien inexistant.
    """
    non_existent_id = 999999  # Un ID qui n'existe probablement pas

    response = await async_client.get(f"/mathematicien/{non_existent_id}")

    assert response.status_code == 404
    res_data = response.json()
    assert res_data["success"] is False
    assert "error" in res_data
