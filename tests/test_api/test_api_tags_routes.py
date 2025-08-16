import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tags(async_client: AsyncClient, ):
    # Vérification de la route /tags/add et /tags/all' qui crée et récupère les tags
    payload = {
        "tag_name": "tag1"
    }
    response = await async_client.post("/tags/add", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Vérification que le tag a été ajouté
    response = await async_client.get("/tags/all")
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]
    assert isinstance(tags, list)
    assert len(tags) >= 1
    assert any(t["tag"] == payload["tag_name"] for t in tags)

#If the Tag already exists
@pytest.mark.asyncio
async def test_create_tags(async_client: AsyncClient, ):
    # Vérification de la route /tags/add et /tags/all' qui crée et récupère les tags
    payload = {
        "tag_name": "tag1"
    }
    response1 = await async_client.post("/tags/add", json=payload)
    assert response1.status_code == 200
    data = response1.json()
    assert data["success"] is True
    response2 = await async_client.post("/tags/add", json=payload)
    assert response2.status_code == 409
    data = response2.json()
    assert data["success"] is False
    assert "error" in data
    assert "Tag already exists" in data["error"]

@pytest.mark.asyncio
async def test_get_tag_of_concept(async_client, setup_test_concept, setup_tag_concept):
    response = await async_client.get(f"/tags/name/concept_id/{setup_test_concept['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]


@pytest.mark.asyncio
async def test_get_tag_no_concept(async_client):
    wrong_id = 999999
    response = await async_client.get(f"/tags/name/concept_id/{str(wrong_id)}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]


@pytest.mark.asyncio
async def test_get_no_tag_of_concept(async_client, setup_test_concept):
    response = await async_client.get(f"/tags/name/concept_id/{setup_test_concept['id']}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "No tags found" in data["error"]


@pytest.mark.asyncio
async def test_get_id_tag_concept(async_client, setup_tag_concept, setup_test_concept):
    response = await async_client.get(f"/tags/id/concept_id/{setup_test_concept['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]


@pytest.mark.asyncio
async def test_get_id_no_concept(async_client, ):
    wrong_id = 999999
    response = await async_client.get(f"/tags/id/concept_id/{str(wrong_id)}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]


@pytest.mark.asyncio
async def test_get_id_no_tag_concept(async_client, setup_test_concept):
    response = await async_client.get(f"/tags/id/concept_id/{setup_test_concept['id']}")
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "No tags found" in data["error"]


@pytest.mark.asyncio
async def test_delete_tag(transaction, async_client, setup_test_concept, setup_tag_concept):
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/remove/concept", json=payload)
    assert response.status_code == 200
    async with transaction.cursor() as cur:
        await cur.execute("SELECT * FROM concept_tags WHERE concept_id = %s AND tag_id = %s;",
                          (setup_test_concept["id"], setup_tag_concept["id"]))
        data = await cur.fetchone()
        assert data is None, "La suppression du lien entre concept et Tag a échoué"

@pytest.mark.asyncio
async def test_delete_tag_no_relation(transaction, async_client, setup_test_concept, setup_tag):
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/remove/concept", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Relation does not exist for this concept and tag" in data["error"]

@pytest.mark.asyncio
async def test_delete_tag_no_concept(transaction, async_client, setup_test_concept, setup_tag):
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]+1
    }
    response = await async_client.post(url="/tags/remove/concept", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]

@pytest.mark.asyncio
async def test_delete_tag_no_tag(transaction, async_client, setup_test_concept, setup_tag):
    payload = {
        "tag_id": setup_tag["id"]+999,
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/remove/concept", json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Tag introuvable" in data["error"]

@pytest.mark.asyncio
async def test_get_all_tags(transaction, async_client, setup_test_concept, setup_tag_concept):
    response = await async_client.get(url="/tags/all")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]
    assert isinstance(tags, list)
    assert len(tags) >= 1

@pytest.mark.asyncio
async def test_add_relation_concept_tag(async_client,setup_test_concept,setup_tag_concept):
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/add/concept",json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False

@pytest.mark.asyncio
async def test_add_relation_concept_tag_alreadyExist(async_client,setup_test_concept,setup_tag_concept):
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/add/concept",json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Relation already exists" in data["error"]

@pytest.mark.asyncio
async def test_add_relation_concept_tag_TagnotExist(async_client,setup_test_concept,setup_tag):
    payload = {
        "tag_id": setup_tag["id"]+1,
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/add/concept",json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Tag introuvable" in data["error"]

@pytest.mark.asyncio
async def test_add_relation_concept_tag_ConceptnotExist(async_client,setup_test_concept,setup_tag):
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]+1
    }
    response = await async_client.post(url="/tags/add/concept",json=payload)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]