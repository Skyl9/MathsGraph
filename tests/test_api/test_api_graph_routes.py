import json
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Relation


@pytest.mark.asyncio
@patch("app.api.routes.graph_routes.redis_db.get", new_callable=AsyncMock)
@patch("app.api.routes.graph_routes.redis_db.set", new_callable=AsyncMock)
async def test_get_graph_success(mock_redis_set, mock_redis_get, async_client: AsyncClient, setup_graph):
    """
    Vérifie que tout va bien avec la route GET /graph avec uniquement des noeuds (Cache Miss).
    """
    # On simule un cache vide (pour forcer l'appel à la BDD)
    mock_redis_get.return_value = None

    response = await async_client.get("/graph")
    assert response.status_code == 200
    resData = response.json()

    assert resData["success"] is True
    data = resData["data"]

    assert data["nodes"] is not None
    assert "edges" in data

    nodes = data["nodes"]
    assert len(nodes) >= 1
    assert any(node["id"] == setup_graph["id"] for node in nodes)

    # 🌟 On vérifie que le backend a bien essayé de sauvegarder en cache
    assert mock_redis_get.called
    assert mock_redis_set.called


@pytest.mark.asyncio
@patch("app.api.routes.graph_routes.redis_db.get", new_callable=AsyncMock)
@patch("app.api.routes.graph_routes.redis_db.set", new_callable=AsyncMock)
async def test_get_graph_with_edges(mock_redis_set, mock_redis_get, db_session: AsyncSession, async_client: AsyncClient, setup_two_concepts):
    """
    Vérifie que la route GET /graph renvoie bien les arêtes s'il y a des relations.
    """
    mock_redis_get.return_value = None

    concept1_id = setup_two_concepts["concept1_id"]
    concept2_id = setup_two_concepts["concept2_id"]

    new_rel = Relation(
        concept_source=concept1_id,
        concept_cible=concept2_id,
        type_relation="implication",
        description="Test de la route graph"
    )
    db_session.add(new_rel)
    await db_session.commit()

    response = await async_client.get("/graph")
    assert response.status_code == 200

    resData = response.json()
    assert resData["success"] is True

    edges = resData["data"]["edges"]
    assert len(edges) >= 1

    found_edge = next((e for e in edges if e["start"] == concept1_id and e["end"] == concept2_id), None)
    assert found_edge is not None
    assert found_edge["type"] == "implication"


@pytest.mark.asyncio
@patch("app.api.routes.graph_routes.redis_db.get", new_callable=AsyncMock)
async def test_get_graph_from_cache(mock_redis_get, async_client: AsyncClient):
    """
    Vérifie que la route sert directement la donnée depuis Redis si elle existe.
    """
    # On fabrique un faux graphe JSON
    fake_cached_data = {
        "nodes": [{"id": 999, "nom": "Théorème de Test Cache", "typeMath": "type", "position": {}}],
        "edges": []
    }
    # On ordonne au Mock de renvoyer ça comme si c'était Redis
    mock_redis_get.return_value = json.dumps(fake_cached_data)

    response = await async_client.get("/graph")
    assert response.status_code == 200
    resData = response.json()

    assert resData["success"] is True
    # On vérifie que la meta-donnée indique bien qu'on vient du cache
    assert resData["meta"]["source"] == "cache"
    # On vérifie qu'on a bien reçu notre faux noeud 999
    assert resData["data"]["nodes"][0]["id"] == 999
