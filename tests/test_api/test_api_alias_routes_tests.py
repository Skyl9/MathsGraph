import pytest
from httpx import AsyncClient

from tests.utils import create_headers_token


# La fixture 'async_client' doit être définie dans votre conftest.py
# La fixture 'setup_test_concept' est nécessaire pour avoir un concept_id valide
# pour associer l'alias. Assurez-vous qu'elle est définie dans conftest.py,
# comme dans l'exemple fourni précédemment.

@pytest.mark.asyncio
async def test_create_alias_success(async_client: AsyncClient, setup_test_concept,setup_user_token_admin):
    """
    Teste la création réussie d'un alias.
    """
    header = create_headers_token(setup_user_token_admin)
    concept_id = setup_test_concept["id"]
    alias_data = {
        "id": concept_id,  # concept_id dans la base de données
        "value": "new_unique_alias"
    }

    response = await async_client.post("/alias", json=alias_data,headers=header)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert data["data"] is None # La route retourne None pour 'data' en cas de succès

    # Optionnel: Vérifier que l'alias a bien été créé en le recherchant directement dans la DB
    # (Cela nécessiterait une fixture de connexion DB ou une route de lecture d'alias)


@pytest.mark.asyncio
async def test_create_alias_duplicate(async_client: AsyncClient, setup_test_concept,setup_user_token_admin):
    """
    Teste la tentative de création d'un alias déjà existant.
    """
    header = create_headers_token(setup_user_token_admin)
    concept_id = setup_test_concept["id"]
    alias_data = {
        "id": concept_id,
        "value": "duplicate_alias_test"
    }

    # Créer l'alias une première fois
    response = await async_client.post("/alias", json=alias_data,headers=header)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Tenter de créer le même alias une deuxième fois
    response = await async_client.post("/alias", json=alias_data,headers=header)
    

    assert response.status_code == 409 # ConflictException a bien lever l'exception
    data = response.json()
    print(data)
    assert data["success"] is False
    assert "error" in data
    assert "Alias already exists" in data["error"]


