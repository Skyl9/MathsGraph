import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Relation, Concept

from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_create_relation_success(
    async_client: AsyncClient, setup_two_concepts: dict, db_session: AsyncSession, setup_user_token_admin
):
    """
    Teste la création réussie d'une relation.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept1_name = setup_two_concepts["concept1_name"]
    concept2_name = setup_two_concepts["concept2_name"]
    relation_type = "implication"
    description = "Ce test vérifie l'implication entre les concepts."

    payload = {
        "value": {"théo1": concept1_name, "théo2": concept2_name, "relation": relation_type, "desc": description}
    }

    response = await async_client.post("/relations", json=payload, headers=headers)

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"] is None
    assert res_data["error"] is None

    # Vérifier que la relation a bien été ajoutée à la base de données
    query = select(Relation).join(Concept, Relation.concept_source == Concept.id).where(Concept.nom == concept1_name)
    result = await db_session.execute(query)
    db_relation = result.scalars().first()

    assert db_relation is not None
    assert db_relation.type_relation == relation_type
    assert db_relation.description == description


@pytest.mark.asyncio
async def test_create_relation_concept_not_found(
    async_client: AsyncClient, setup_two_concepts: dict, setup_user_token_admin
):
    """
    Teste la création d'une relation lorsque un ou les deux concepts n'existent pas.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept_existant_name = setup_two_concepts["concept1_name"]
    concept_non_existant_name = "ConceptInexistant"
    relation_type = "equivalence"

    # Cas 1 : Concept source non trouvé
    payload1 = {
        "value": {
            "théo1": concept_non_existant_name,
            "théo2": concept_existant_name,
            "relation": relation_type,
            "desc": "Test avec source inexistante",
        }
    }
    response1 = await async_client.post("/relations", json=payload1, headers=headers)
    assert response1.status_code == 404
    assert "Concept not found" in response1.json()["error"]

    # Cas 2 : Concept cible non trouvé
    payload2 = {
        "value": {
            "théo1": concept_existant_name,
            "théo2": concept_non_existant_name,
            "relation": relation_type,
            "desc": "Test avec cible inexistante",
        }
    }
    response2 = await async_client.post("/relations", json=payload2, headers=headers)
    assert response2.status_code == 404
    assert "Concept not found" in response2.json()["error"]


@pytest.mark.asyncio
async def test_create_relation_conflict(async_client: AsyncClient, setup_two_concepts: dict, setup_user_token_admin):
    """
    Teste la création d'une relation qui existe déjà.
    """
    headers = create_headers_token(setup_user_token_admin)
    concept1_name = setup_two_concepts["concept1_name"]
    concept2_name = setup_two_concepts["concept2_name"]
    relation_type = "reciproque"
    description = "Description pour relation existante"

    payload = {
        "value": {"théo1": concept1_name, "théo2": concept2_name, "relation": relation_type, "desc": description}
    }

    # Créer la relation une première fois avec succès
    first_response = await async_client.post("/relations", json=payload, headers=headers)
    assert first_response.status_code == 201

    # Tenter de créer la même relation une seconde fois
    second_response = await async_client.post("/relations", json=payload, headers=headers)

    assert second_response.status_code == 409  # Code pour ConflictException
    assert "Relation already exists" in second_response.json()["error"]
