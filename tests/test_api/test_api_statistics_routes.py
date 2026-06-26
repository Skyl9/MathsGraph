import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_stats(async_client: AsyncClient, setup_test_concept):
    concept_id = setup_test_concept["id"]
    response = await async_client.get("/statistics/concepts/" + str(concept_id))
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True

    assert "data" in data
    data = data["data"]
    assert data["total_views"] == 0


@pytest.mark.asyncio
async def test_get_stats_not_found(async_client: AsyncClient):
    false_concept_id = 99999
    response = await async_client.get("/statistics/concepts/" + str(false_concept_id))
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept not found" in data["error"]
