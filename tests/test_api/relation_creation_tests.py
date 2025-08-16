import pytest
from httpx import AsyncClient
from psycopg import AsyncConnection





@pytest.mark.asyncio
async def test_create_relation_success(async_client: AsyncClient, setup_two_concepts:dict, transaction: AsyncConnection):
    """
    Teste la création réussie d'une relation.
    """
    concept1_name = setup_two_concepts["concept1_name"]
    concept2_name = setup_two_concepts["concept2_name"]
    relation_type = "implication"
    description = "Ce test vérifie l'implication entre les concepts."

    payload = {
        "value": {
            "théo1": concept1_name,
            "théo2": concept2_name,
            "relation": relation_type,
            "desc": description
        }
    }

    response = await async_client.post("/relation/create", json=payload)

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"] is None
    assert res_data["error"] is None

    # Vérifier que la relation a bien été ajoutée à la base de données
    async with transaction.cursor() as cur:
        await cur.execute(
            """
            SELECT r.type_relation, r.description, cs.nom, cc.nom
            FROM relations r
            JOIN concepts cs ON r.concept_source = cs.id
            JOIN concepts cc ON r.concept_cible = cc.id
            WHERE cs.nom = %s AND cc.nom = %s;
            """,
            (concept1_name, concept2_name)
        )
        db_relation = await cur.fetchone()

    assert db_relation is not None
    assert db_relation[0] == relation_type
    assert db_relation[1] == description
    assert db_relation[2] == concept1_name
    assert db_relation[3] == concept2_name


@pytest.mark.asyncio
async def test_create_relation_concept_not_found(async_client: AsyncClient, setup_two_concepts: dict):
    """
    Teste la création d'une relation lorsque un ou les deux concepts n'existent pas.
    """
    concept_existant_name = setup_two_concepts["concept1_name"]
    concept_non_existant_name = "ConceptInexistant"
    relation_type = "equivalence"

    # Cas 1 : Concept source non trouvé
    payload1 = {
        "value": {
            "théo1": concept_non_existant_name,
            "théo2": concept_existant_name,
            "relation": relation_type,
            "desc": "Test avec source inexistante"
        }
    }
    response1 = await async_client.post("/relation/create", json=payload1)
    assert response1.status_code == 404
    assert "Concept not found" in response1.json()["error"]

    # Cas 2 : Concept cible non trouvé
    payload2 = {
        "value": {
            "théo1": concept_existant_name,
            "théo2": concept_non_existant_name,
            "relation": relation_type,
            "desc": "Test avec cible inexistante"
        }
    }
    response2 = await async_client.post("/relation/create", json=payload2)
    assert response2.status_code == 404
    assert "Concept not found" in response2.json()["error"]

    # Cas 3 : Les deux concepts non trouvés
    payload3 = {
        "value": {
            "théo1": "AutreConceptInexistant1",
            "théo2": "AutreConceptInexistant2",
            "relation": relation_type,
            "desc": "Test avec les deux inexistants"
        }
    }
    response3 = await async_client.post("/relation/create", json=payload3)
    assert response3.status_code == 404
    assert "Concept not found" in response3.json()["error"]


@pytest.mark.asyncio
async def test_create_relation_conflict(async_client: AsyncClient, setup_two_concepts: dict):
    """
    Teste la création d'une relation qui existe déjà.
    """
    concept1_name = setup_two_concepts["concept1_name"]
    concept2_name = setup_two_concepts["concept2_name"]
    relation_type = "reciproque"
    description = "Description pour relation existante"

    payload = {
        "value": {
            "théo1": concept1_name,
            "théo2": concept2_name,
            "relation": relation_type,
            "desc": description
        }
    }

    # Créer la relation une première fois avec succès
    first_response = await async_client.post("/relation/create", json=payload)
    assert first_response.status_code == 200

    # Tenter de créer la même relation une seconde fois
    second_response = await async_client.post("/relation/create", json=payload)

    assert second_response.status_code == 409  # Code pour ConflictException
    assert "Relation already exists" in second_response.json()["error"]
