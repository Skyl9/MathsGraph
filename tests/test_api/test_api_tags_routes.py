import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import concept_tags
from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_create_tags(async_client: AsyncClient, setup_user_token_admin):
    # Vérification de la route /tags/add et /tags/all' qui crée et récupère les tags
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_name": "tag1"
    }
    response = await async_client.post("/tags", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Vérification que le tag a été ajouté
    response = await async_client.get("/tags/all", headers=headers)
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]
    assert isinstance(tags, list)
    assert len(tags) >= 1
    assert any(t["tag"] == payload["tag_name"] for t in tags)

#If the Tag already exists
@pytest.mark.asyncio
async def test_create_tags_conflict(async_client: AsyncClient, setup_user_token_admin):
    # Vérification de la route /tags/add et /tags/all' qui crée et récupère les tags
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_name": "tag1"
    }
    response1 = await async_client.post("/tags", json=payload, headers=headers)
    assert response1.status_code == 200
    data = response1.json()
    assert data["success"] is True
    response2 = await async_client.post("/tags", json=payload, headers=headers)
    assert response2.status_code == 409
    data = response2.json()
    assert data["success"] is False
    assert "error" in data
    assert "Tag already exists" in data["error"]

@pytest.mark.asyncio
async def test_get_tag_of_concept(async_client, setup_test_concept, setup_tag_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get(f"/tags/name/concept_id/{setup_test_concept['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]


@pytest.mark.asyncio
async def test_get_tag_no_concept(async_client, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    wrong_id = 999999
    response = await async_client.get(f"/tags/name/concept_id/{str(wrong_id)}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]


@pytest.mark.asyncio
async def test_get_no_tag_of_concept(async_client, setup_test_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get(f"/tags/name/concept_id/{setup_test_concept['id']}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "No tags found" in data["error"]


@pytest.mark.asyncio
async def test_get_id_tag_concept(async_client, setup_tag_concept, setup_test_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get(f"/tags/id/concept_id/{setup_test_concept['id']}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]


@pytest.mark.asyncio
async def test_get_id_no_concept(async_client, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    wrong_id = 999999
    response = await async_client.get(f"/tags/id/concept_id/{str(wrong_id)}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]


@pytest.mark.asyncio
async def test_get_id_no_tag_concept(async_client, setup_test_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get(f"/tags/id/concept_id/{setup_test_concept['id']}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "No tags found" in data["error"]


@pytest.mark.asyncio
async def test_delete_tag(db_session: AsyncSession, async_client, setup_test_concept, setup_tag_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.delete(url=f"/tags/concept/{payload["concept_id"]}/tag/{payload["tag_id"]}", headers=headers)
    assert response.status_code == 200
    
    query = select(concept_tags).where(
        concept_tags.c.concept_id == setup_test_concept["id"],
        concept_tags.c.tag_id == setup_tag_concept["id"]
    )
    result = await db_session.execute(query)
    assert result.first() is None, "La suppression du lien entre concept et Tag a échoué"

@pytest.mark.asyncio
async def test_delete_tag_no_relation(async_client, setup_test_concept, setup_tag, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.delete(url=f"/tags/concept/{payload["concept_id"]}/tag/{payload["tag_id"]}", headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Relation does not exist for this concept and tag" in data["error"]

@pytest.mark.asyncio
async def test_delete_tag_no_concept(async_client, setup_test_concept, setup_tag, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]+1
    }
    response = await async_client.delete(url=f"/tags/concept/{payload["concept_id"]}/tag/{payload["tag_id"]}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]

@pytest.mark.asyncio
async def test_delete_tag_no_tag(async_client, setup_test_concept, setup_tag, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag["id"]+999,
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.delete(url=f"/tags/concept/{payload["concept_id"]}/tag/{payload["tag_id"]}", headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Tag introuvable" in data["error"]

@pytest.mark.asyncio
async def test_get_all_tags(async_client, setup_test_concept, setup_tag_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get(url="/tags/all", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    tags = data["data"]
    assert isinstance(tags, list)
    assert len(tags) >= 1

@pytest.mark.asyncio
async def test_add_relation_concept_tag(async_client,setup_test_concept,setup_tag_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/concept",json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False

@pytest.mark.asyncio
async def test_add_relation_concept_tag_alreadyExist(async_client,setup_test_concept,setup_tag_concept, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag_concept["id"],
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/concept",json=payload, headers=headers)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert "Relation already exists" in data["error"]

@pytest.mark.asyncio
async def test_add_relation_concept_tag_TagnotExist(async_client,setup_test_concept,setup_tag, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag["id"]+1,
        "concept_id": setup_test_concept["id"]
    }
    response = await async_client.post(url="/tags/concept",json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Tag introuvable" in data["error"]

@pytest.mark.asyncio
async def test_add_relation_concept_tag_ConceptnotExist(async_client,setup_test_concept,setup_tag, setup_user_token_admin):
    headers = create_headers_token(setup_user_token_admin)
    payload = {
        "tag_id": setup_tag["id"],
        "concept_id": setup_test_concept["id"]+1
    }
    response = await async_client.post(url="/tags/concept",json=payload, headers=headers)
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "Concept introuvable" in data["error"]
