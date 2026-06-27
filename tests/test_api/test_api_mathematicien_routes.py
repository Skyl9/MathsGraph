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
    response = await async_client.post("/mathematiciens", json={"value": test_name}, headers=headers)

    assert response.status_code == 201
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

    response = await async_client.get(f"/mathematiciens/{mathematicien_id}")

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

    response = await async_client.get(f"/mathematiciens/{non_existent_id}")

    assert response.status_code == 404
    res_data = response.json()
    assert res_data["success"] is False
    assert "error" in res_data


@pytest.mark.asyncio
async def test_get_mathematiciens_timeline(async_client: AsyncClient, db_session: AsyncSession):
    """
    Teste la récupération de la timeline des mathématiciens.
    """
    # Create a mathematician with date_naissance
    from datetime import date

    new_math = Mathematicien(nom="Timeline Math", date_naissance=date(1990, 1, 1))
    db_session.add(new_math)
    await db_session.commit()

    response = await async_client.get("/mathematiciens/timeline/all")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"], list)
    # The setup_test_mathematicien should be in the list
    assert any(m["nom"] == "Timeline Math" for m in res_data["data"])


@pytest.mark.asyncio
async def test_update_mathematicien_success(
    async_client: AsyncClient, setup_test_mathematicien: dict, setup_user_token_admin
):
    """
    Teste la mise à jour d'un mathématicien.
    """
    headers = create_headers_token(setup_user_token_admin)
    mathematicien_id = setup_test_mathematicien["id"]
    payload = {"field": "nom", "value": "Alan Turing Modifié"}

    response = await async_client.patch(f"/mathematiciens/{mathematicien_id}", json=payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True


@pytest.mark.asyncio
async def test_get_all_mathematiciens_name(async_client: AsyncClient, setup_test_mathematicien: dict):
    """
    Teste la récupération de tous les noms de mathématiciens.
    """
    response = await async_client.get("/mathematiciens/")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert isinstance(res_data["data"], list)
    assert any(m["nom"] == setup_test_mathematicien["nom"] for m in res_data["data"])


@pytest.mark.asyncio
async def test_get_mathematicien_by_name(async_client: AsyncClient, setup_test_mathematicien: dict):
    """
    Teste la récupération d'un mathématicien par nom.
    """
    name = setup_test_mathematicien["nom"]
    response = await async_client.get(f"/mathematiciens/name/{name}")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    # The route returns MathematicienResponse, so data is an object
    assert res_data["data"]["id"] == setup_test_mathematicien["id"]
