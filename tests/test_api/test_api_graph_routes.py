import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_graph_success(transaction,async_client: AsyncClient, setup_graph):
    """
    Vérifie que tout va bien avec la route GET /graph
    :param transaction:
    :param async_client:
    :param setup_graph:
    :return:
    """
    response = await async_client.get("/graph")
    assert response.status_code == 200
    resData = response.json()

    assert resData["success"] is True
    assert resData["data"] is not None
    data = resData["data"]
    assert data["nodes"] is not None
    nodes = data["nodes"]
    assert len(nodes) == 1, "Duplication d'un élément dans la liste des nodes"
    assert nodes[0]["id"] == setup_graph["id"]
    assert nodes[0]["nom"] == setup_graph["nom"]
    async with transaction.cursor() as cur:
        await cur.execute("SELECT type FROM type WHERE type.id = %s", (setup_graph["type_id"],))
        typeR = await cur.fetchone()
        assert typeR is not None
    assert nodes[0]["typeMath"] == typeR[0], "Erreur dans l'enregristrement du type"
    assert nodes[0]["position"]["grille"] == setup_graph["position"], "Erreur dans l'enregristrement des positios"
