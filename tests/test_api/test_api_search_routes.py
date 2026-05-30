import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_quick_search_success(async_client: AsyncClient, setup_test_concept):
    """
    Teste la recherche rapide avec un terme correspondant au concept de base.
    """
    response = await async_client.get(f"/search/quick?q={setup_test_concept['nom'][:3]}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    # Le concept devrait être dans les résultats
    assert any(c["nom"] == setup_test_concept["nom"] for c in data["data"])

@pytest.mark.asyncio
async def test_advanced_search_success(async_client: AsyncClient, setup_test_concept):
    """
    Teste la recherche avancée avec un payload complet.
    """
    payload = {
        "query": setup_test_concept["nom"][:4],
        "filters": {
            "concept": True,
            "mathematicien": False,
            "category": False
        }
    }
    
    response = await async_client.post("/search/advanced", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "data" in data
    assert isinstance(data["data"], list)
    # Le concept devrait être dans les résultats
    assert any(c["nom"] == setup_test_concept["nom"] for c in data["data"])
    assert all(c["entity_type"] == "concept" for c in data["data"])
