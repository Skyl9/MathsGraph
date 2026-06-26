import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Source, concepts_sources

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_create_source_success(
    async_client: AsyncClient, setup_test_concept: dict, db_session: AsyncSession, setup_user_token_admin
):
    """
    Teste la création réussie d'une nouvelle source et sa liaison à un concept.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept_id = setup_test_concept["id"]
    source_data = {
        "value": {
            "source": "Titre du livre de test",
            "auteur": "Auteur Fictif",
            "annee": 2023,
            "url": "http://example.com/test-source",
            "type": "livre",
            "id": concept_id,  # ID du concept à lier
        }
    }

    response = await async_client.post("/source", json=source_data, headers=headers)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"] is None
    assert res_data["error"] is None

    # Vérifier que la source a bien été ajoutée et liée au concept dans la base de données
    query_src = select(Source).where(Source.titre == source_data["value"]["source"])
    result_src = await db_session.execute(query_src)
    db_source = result_src.scalars().first()

    assert db_source is not None
    source_id = db_source.id
    assert db_source.titre == source_data["value"]["source"]
    assert db_source.auteur == source_data["value"]["auteur"]
    assert db_source.annee == source_data["value"]["annee"]
    assert db_source.url == source_data["value"]["url"]
    assert db_source.type == source_data["value"]["type"]

    query_link = select(concepts_sources).where(
        concepts_sources.c.concept_id == concept_id, concepts_sources.c.source_id == source_id
    )
    result_link = await db_session.execute(query_link)
    db_concept_source_link = result_link.first()
    assert db_concept_source_link is not None


@pytest.mark.asyncio
async def test_create_source_conflict(async_client: AsyncClient, setup_test_concept: dict, setup_user_token_admin):
    """
    Teste la tentative de créer une source avec un titre qui existe déjà.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept_id = setup_test_concept["id"]
    source_title = "Titre source existante"
    source_data = {
        "value": {
            "source": source_title,
            "auteur": "Auteur Dupliqué",
            "annee": 2020,
            "url": "http://example.com/duplicate",
            "type": "article",
            "id": concept_id,
        }
    }

    # Créer la source une première fois (doit réussir)
    first_response = await async_client.post("/source", json=source_data, headers=headers)
    assert first_response.status_code == 200
    assert first_response.json()["success"] is True

    # Tenter de créer la même source une seconde fois (doit échouer avec un conflit)
    second_response = await async_client.post("/source", json=source_data, headers=headers)

    assert second_response.status_code == 409  # Code HTTP pour ConflictException
    res_data = second_response.json()
    assert res_data["success"] is False
    assert "error" in res_data
    assert "Source already exists" in res_data["error"]


@pytest.mark.asyncio
async def test_create_source_invalid_concept_id(async_client: AsyncClient, setup_user_token_admin):
    """
    Teste la création d'une source avec un ID de concept qui n'existe pas.
    Cela devrait entraîner une erreur car le concept ne sera pas trouvé par get_id_by_field.
    """
    headers = create_headers_token(setup_user_token_admin)
    non_existent_concept_id = 999999999  # Un ID qui n'existe probablement pas
    source_data = {
        "value": {
            "source": "Source pour concept inexistant",
            "auteur": "Auteur Invalide",
            "annee": 2024,
            "url": "http://example.com/invalid",
            "type": "livre",
            "id": non_existent_concept_id,  # ID de concept non valide
        }
    }

    response = await async_client.post("/source", json=source_data, headers=headers)

    assert response.status_code == 404
    res_data = response.json()
    assert res_data["success"] is False
    assert "error" in res_data


@pytest.mark.asyncio
async def test_create_source_wrong_type(async_client: AsyncClient, setup_test_concept: dict, setup_user_token_admin):
    """
    Teste la tentative de créer une source avec un type non autorisé.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept_id = setup_test_concept["id"]
    source_data = {
        "value": {
            "source": "Source mauvais type",
            "auteur": "Auteur",
            "annee": 2020,
            "url": "http://example.com",
            "type": "mauvais type",
            "id": concept_id,
        }
    }

    response = await async_client.post("/source", json=source_data, headers=headers)
    assert response.status_code == 400
    res_json = response.json()
    assert res_json["success"] is False
    assert "error" in res_json
    assert "Type not allowed" in res_json["error"]
