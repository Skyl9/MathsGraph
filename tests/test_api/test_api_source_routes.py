import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection

# Les fixtures comme async_client et setup_test_concept sont supposées être
# définies dans votre fichier conftest.py et disponibles ici.

@pytest.mark.asyncio
async def test_create_source_success(async_client: AsyncClient, setup_test_concept: dict, transaction: AsyncConnection):
    """
    Teste la création réussie d'une nouvelle source et sa liaison à un concept.
    """
    concept_id = setup_test_concept["id"]
    source_data = {
        "value": {
            "source": "Titre du livre de test",
            "auteur": "Auteur Fictif",
            "annee": 2023,
            "url": "http://example.com/test-source",
            "type": "livre",
            "id": concept_id # ID du concept à lier
        }
    }

    response = await async_client.post("/source/create", json=source_data)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"] is None
    assert res_data["error"] is None

    # Vérifier que la source a bien été ajoutée et liée au concept dans la base de données
    async with transaction.cursor() as cur:
        await cur.execute("SELECT id, titre, auteur, annee, url, type FROM sources WHERE titre = %s;", (source_data["value"]["source"],))
        db_source = await cur.fetchone()

        assert db_source is not None
        source_id = db_source[0]
        assert db_source[1] == source_data["value"]["source"]
        assert db_source[2] == source_data["value"]["auteur"]
        assert db_source[3] == source_data["value"]["annee"]
        assert db_source[4] == source_data["value"]["url"]
        assert db_source[5] == source_data["value"]["type"]

        await cur.execute("SELECT concept_id, source_id FROM concepts_sources WHERE concept_id = %s AND source_id = %s;", (concept_id, source_id))
        db_concept_source_link = await cur.fetchone()
        assert db_concept_source_link is not None
        assert db_concept_source_link[0] == concept_id
        assert db_concept_source_link[1] == source_id

    # Nettoyage supplémentaire (la fixture transaction gérera le rollback, mais c'est pour l'exemple si vous n'aviez pas de transaction)
    # async with transaction.cursor() as cur:
    #     await cur.execute("DELETE FROM concepts_sources WHERE concept_id = %s AND source_id = %s;", (concept_id, source_id))
    #     await cur.execute("DELETE FROM sources WHERE id = %s;", (source_id,))
    #     await transaction.commit()


@pytest.mark.asyncio
async def test_create_source_conflict(async_client: AsyncClient, setup_test_concept: dict):
    """
    Teste la tentative de créer une source avec un titre qui existe déjà.
    """
    concept_id = setup_test_concept["id"]
    source_title = "Titre source existante"
    source_data = {
        "value": {
            "source": source_title,
            "auteur": "Auteur Dupliqué",
            "annee": 2020,
            "url": "http://example.com/duplicate",
            "type": "article",
            "id": concept_id
        }
    }

    # Créer la source une première fois (doit réussir)
    first_response = await async_client.post("/source/create", json=source_data)
    assert first_response.status_code == 200
    assert first_response.json()["success"] is True

    # Tenter de créer la même source une seconde fois (doit échouer avec un conflit)
    second_response = await async_client.post("/source/create", json=source_data)

    assert second_response.status_code == 409 # Code HTTP pour ConflictException
    res_data = second_response.json()
    assert res_data["success"] is False
    assert "error" in res_data
    assert "Source already exists" in res_data["error"]


@pytest.mark.asyncio
async def test_create_source_invalid_concept_id(async_client: AsyncClient,):
    """
    Teste la création d'une source avec un ID de concept qui n'existe pas.
    Cela devrait entraîner une erreur interne car la liaison échouera.
    """
    non_existent_concept_id = 999999999 # Un ID qui n'existe probablement pas
    source_data = {
        "value": {
            "source": "Source pour concept inexistant",
            "auteur": "Auteur Invalide",
            "annee": 2024,
            "url": "http://example.com/invalid",
            "type": "livre",
            "id": non_existent_concept_id # ID de concept non valide
        }
    }

    response = await async_client.post("/source/create", json=source_data)

    assert response.status_code == 404 # Attendu car une exception interne (e.g., violation de FK)
    res_data = response.json()
    assert res_data["success"] is False
    assert "error" in res_data
    # Le message d'erreur exact peut varier en fonction de la base de données et de la configuration de l'exception.
    # Il est probable que ce soit une erreur liée à la contrainte de clé étrangère.

@pytest.mark.asyncio
async def test_create_source_wrong_type(async_client: AsyncClient, setup_test_concept: dict):
    """
    Teste la tentative de créer une source avec un titre qui existe déjà.
    """
    concept_id = setup_test_concept["id"]
    source_title = "Titre source existante"
    source_data = {
        "value": {
            "source": source_title,
            "auteur": "Auteur Dupliqué",
            "annee": 2020,
            "url": "http://example.com/duplicate",
            "type": "mauvais type",
            "id": concept_id
        }
    }

    response = await async_client.post("/source/create", json=source_data)
    assert response.status_code == 400
    response = response.json()
    assert response["success"] is False
    assert "error" in response
    assert "Type not allowed" in response["error"]