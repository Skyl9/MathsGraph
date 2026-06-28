import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_create_and_get_draft(async_client: AsyncClient, setup_user_token_admin, setup_test_concept):
    token = setup_user_token_admin["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create draft
    draft_payload = {
        "concept_id": setup_test_concept["id"],
        "draft_data": {"enonce": "Nouvel énoncé", "nom": "Concept test"},
    }

    response = await async_client.post("/api/drafts/", json=draft_payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    draft_id = data["data"]["id"]

    # Get draft
    response = await async_client.get(f"/api/drafts/{draft_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["draft_data"]["enonce"] == "Nouvel énoncé"


@pytest.mark.asyncio
async def test_update_draft(async_client: AsyncClient, setup_user_token_admin, setup_test_concept):
    token = setup_user_token_admin["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Create draft
    draft_payload = {"concept_id": setup_test_concept["id"], "draft_data": {"enonce": "Nouvel énoncé"}}
    create_resp = await async_client.post("/api/drafts/", json=draft_payload, headers=headers)
    draft_id = create_resp.json()["data"]["id"]

    # Update draft
    update_payload = {"draft_data": {"enonce": "Enoncé modifié"}}
    response = await async_client.patch(f"/api/drafts/{draft_id}", json=update_payload, headers=headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["draft_data"]["enonce"] == "Enoncé modifié"


@pytest.mark.asyncio
async def test_publish_draft(async_client: AsyncClient, setup_user_token_admin, setup_test_concept):
    token = setup_user_token_admin["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    draft_payload = {"concept_id": setup_test_concept["id"], "draft_data": {"enonce": "Enoncé publié via brouillon"}}
    create_resp = await async_client.post("/api/drafts/", json=draft_payload, headers=headers)
    draft_id = create_resp.json()["data"]["id"]

    response = await async_client.post(f"/api/drafts/{draft_id}/publish", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    # Verify draft is deleted
    get_resp = await async_client.get(f"/api/drafts/{draft_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_draft(async_client: AsyncClient, setup_user_token_admin, setup_test_concept):
    token = setup_user_token_admin["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    draft_payload = {"concept_id": setup_test_concept["id"], "draft_data": {"enonce": "A supprimer"}}
    create_resp = await async_client.post("/api/drafts/", json=draft_payload, headers=headers)
    draft_id = create_resp.json()["data"]["id"]

    response = await async_client.delete(f"/api/drafts/{draft_id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK

    get_resp = await async_client.get(f"/api/drafts/{draft_id}", headers=headers)
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND
