import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_graph_success(transaction, async_client: AsyncClient, setup_graph):
    """
    Vérifie que tout va bien avec la route GET /graph avec uniquement des noeuds.
    """
    response = await async_client.get("/graph")
    assert response.status_code == 200
    resData = response.json()

    assert resData["success"] is True
    assert resData["data"] is not None
    data = resData["data"]

    assert data["nodes"] is not None
    assert "edges" in data
    assert isinstance(data["edges"], list)

    nodes = data["nodes"]
    assert len(nodes) == 1, "Duplication d'un élément dans la liste des nodes"
    assert nodes[0]["id"] == setup_graph["id"]
    assert nodes[0]["nom"] == setup_graph["nom"]

    async with transaction.cursor() as cur:
        await cur.execute("SELECT type FROM type WHERE type.id = %s", (setup_graph["type_id"],))
        typeR = await cur.fetchone()
        assert typeR is not None

    assert nodes[0]["typeMath"] == typeR[0], "Erreur dans l'enregistrement du type"
    assert nodes[0]["position"]["grille"] == setup_graph["position"], "Erreur dans l'enregistrement des positions"


# 🌟 NOUVEAU : Un test dédié pour vérifier que les arêtes remontent bien !
@pytest.mark.asyncio
async def test_get_graph_with_edges(transaction, async_client: AsyncClient, setup_two_concepts):
    """
    Vérifie que la route GET /graph renvoie bien les arêtes s'il y a des relations.
    """
    concept1_id = setup_two_concepts["concept1_id"]
    concept2_id = setup_two_concepts["concept2_id"]

    async with transaction.cursor() as cur:
        await cur.execute(
            "INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES (%s, %s, %s, %s)",
            (concept1_id, concept2_id, "implication", "Test de la route graph")
        )

    response = await async_client.get("/graph")
    assert response.status_code == 200

    resData = response.json()
    assert resData["success"] is True

    edges = resData["data"]["edges"]
    assert isinstance(edges, list)
    assert len(edges) >= 1, "Le graphe devrait contenir au moins une arête"

    found_edge = next((e for e in edges if e["start"] == concept1_id and e["end"] == concept2_id), None)

    assert found_edge is not None, "L'arête n'a pas été trouvée dans le graphe"
    assert found_edge["type"] == "implication"