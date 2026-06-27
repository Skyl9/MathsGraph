import pytest
from httpx import AsyncClient

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_get_one_category(async_client: AsyncClient, setup_test_categorie):
    """
    Teste la route GET /category/{id_category} pour s'assurer qu'elle retourne la catégorie correcte.
    """
    category_id = setup_test_categorie["id"]
    response = await async_client.get(f"/categories/{category_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert data["data"]["id"] == category_id
    assert data["data"]["nom"] == setup_test_categorie["nom"]


@pytest.mark.asyncio
async def test_update_category(async_client: AsyncClient, setup_test_categorie, setup_user_token_admin):
    """
    Teste la route PATCH /category/{id_category} pour s'assurer qu'elle met à jour la catégorie.
    """
    headers = create_headers_token(setup_user_token_admin)
    category_id = setup_test_categorie["id"]
    updated_name = "Updated Test Category"
    update_data = {"field": "nom", "value": updated_name, "username": "admin_test"}

    response = await async_client.patch(f"/categories/{category_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None  # Assumant que la route ne retourne pas de données sur succès

    # Vérifier que la catégorie a bien été mise à jour
    response = await async_client.get(f"/categories/{category_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["nom"] == updated_name


@pytest.mark.asyncio
async def test_get_all_categories(async_client: AsyncClient, setup_test_categorie):
    """
    Teste la route GET /category/ pour s'assurer qu'elle retourne une liste de catégories.
    """
    response = await async_client.get("/categories/")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) >= 1  # Au moins la catégorie créée par la fixture

    # Vérifier que la catégorie de test est présente dans la liste
    found_category = False
    for category in data["data"]:
        if category.get("id") == setup_test_categorie["id"]:
            found_category = True
            break
    assert found_category, "La catégorie de test n'a pas été trouvée dans la liste des catégories."


@pytest.mark.asyncio
async def test_create_category(async_client: AsyncClient, setup_user_token_admin):
    """
    Teste la route POST /category/create pour s'assurer qu'elle crée une nouvelle catégorie.
    """
    headers = create_headers_token(setup_user_token_admin)
    new_category_data = {"value": "New Created Category", "description": "Description of a newly created category"}
    response = await async_client.post("/categories", json=new_category_data, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None  # Assumant que la route ne retourne pas de données sur succès

    # Optionnel: Vérifier la création en la récupérant par nom
    response = await async_client.get(f"/categories/name/{new_category_data['value']}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["nom"] == new_category_data["value"]


@pytest.mark.asyncio
async def test_get_category_by_name(async_client: AsyncClient, setup_test_categorie):
    """
    Teste la route GET /category/name/{name} pour s'assurer qu'elle retourne la catégorie correcte.
    """
    category_name = setup_test_categorie["nom"]
    response = await async_client.get(f"/categories/name/{category_name}")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert data["data"]["nom"] == category_name
    assert data["data"]["id"] == setup_test_categorie["id"]
