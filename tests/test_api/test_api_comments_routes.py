import pytest
from httpx import AsyncClient

# Assurez-vous que les fixtures 'async_client', 'setup_test_concept', 'setup_test_user'
# sont définies et disponibles via votre conftest.py.
# La fixture 'setup_test_comment' peut être adaptée pour insérer un commentaire directement dans la DB
# ou en appelant la route API 'add' au début d'un test qui en a besoin.

# Fixture pour créer un commentaire de test via l'API, afin qu'il soit persistant pour les tests suivants
# Cette fixture est une alternative à la fixture 'setup_test_comment' précédente basée sur le service.
# Elle nécessite `async_client` et `setup_test_user` et `setup_test_concept`
@pytest.mark.asyncio
async def test_get_comments_empty(async_client: AsyncClient, setup_test_concept):
    """
    Teste la récupération des commentaires pour un concept sans commentaires.
    """
    concept_id = setup_test_concept["id"]
    response = await async_client.get(f"/comments/{concept_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] == []

@pytest.mark.asyncio
async def test_get_comments_with_data(async_client: AsyncClient,transaction, setup_test_comment, setup_test_concept):
    """
    Teste la récupération des commentaires pour un concept avec des données.
    """
    concept_id = setup_test_concept["id"]
    response = await async_client.get(f"/comments/{concept_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1
    assert data["data"][0]["content"] == setup_test_comment["content"]
    async with transaction.connection.cursor() as cur:
        await cur.execute("SELECT username FROM users WHERE id = %s", (setup_test_comment["user_id"],))
        username = await cur.fetchone()
        assert username is not None
    assert data["data"][0]["username"] == username[0]


# Tests pour la route POST /comments/add/{concept_id}
@pytest.mark.asyncio
async def test_post_comment_success(async_client: AsyncClient, setup_test_concept, setup_test_user):
    """
    Teste l'ajout réussi d'un commentaire.
    """
    concept_id = setup_test_concept["id"]
    comment_data = {
        "content": "This is a new comment via API.",
        "username": setup_test_user["username"],
        "parent_id": None,
        "field": "api_test"
    }
    response = await async_client.post(f"/comments/add/{concept_id}", json=comment_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None

    # Vérifier que le commentaire est bien là en le récupérant
    get_response = await async_client.get(f"/comments/{concept_id}")
    get_data = get_response.json()
    assert any(c["content"] == comment_data["content"] for c in get_data["data"])


@pytest.mark.asyncio
async def test_post_comment_invalid_concept_id(async_client: AsyncClient, setup_test_user):
    """
    Teste l'ajout d'un commentaire avec un concept_id inexistant.
    """
    invalid_concept_id = 99999
    comment_data = {
        "content": "Comment for non-existent concept.",
        "username": setup_test_user["username"],
        "parent_id": None,
        "field": "invalid_test"
    }
    response = await async_client.post(f"/comments/add/{invalid_concept_id}", json=comment_data)
    # Attendre une erreur 500 (InternalServerError) si l'erreur DB n'est pas gérée plus spécifiquement
    assert response.status_code == 404
    data = response.json()
    assert data["success"] is False
    assert "error" in data


# Tests pour la route PATCH /comments/update/{comment_id}
@pytest.mark.asyncio
async def test_patch_comment_success(async_client: AsyncClient, setup_test_comment):
    """
    Teste la mise à jour réussie d'un commentaire.
    """
    comment_id = setup_test_comment["id"]
    updated_content = "Updated content from API."
    update_data = {"content": updated_content}
    response = await async_client.patch(f"/comments/update/{comment_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None

    # Vérifier que le commentaire a été mis à jour
    get_response = await async_client.get(f"/comments/{setup_test_comment['concept_id']}")
    get_data = get_response.json()
    assert any(c["id"] == comment_id and c["content"] == updated_content for c in get_data["data"])

@pytest.mark.asyncio
async def test_patch_comment_not_found(async_client: AsyncClient):
    """
    Teste la mise à jour d'un commentaire inexistant.
    """
    response = await async_client.patch("/comments/update/99999", json={"content": "Non existent"})
    assert response.status_code == 404 # Si NotFoundException est convertie en InternalServerError
    data = response.json()
    assert data["success"] is False
    assert "Commentaire introuvable ou supprimé" in data["error"]


# Tests pour la route DELETE /comments/delete/{comment_id}
@pytest.mark.asyncio
async def test_delete_comment_success(async_client: AsyncClient, setup_test_comment):
    """
    Teste la suppression réussie d'un commentaire.
    """
    comment_id = setup_test_comment["id"]
    concept_id = setup_test_comment["concept_id"]

    response = await async_client.delete(f"/comments/delete/{comment_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"] is None

    # Vérifier que le commentaire est maintenant marqué comme supprimé (et donc non visible via get)
    get_response = await async_client.get(f"/comments/{concept_id}")
    get_data = get_response.json()
    assert not any(c["id"] == comment_id for c in get_data["data"])


@pytest.mark.asyncio
async def test_delete_comment_not_found(async_client: AsyncClient):
    """
    Teste la suppression d'un commentaire inexistant.
    """
    response = await async_client.delete("/comments/delete/99999")
    assert response.status_code == 404 # Si NotFoundException est convertie en InternalServerError
    data = response.json()
    assert data["success"] is False
    assert "Commentaire introuvable" in data["error"]


@pytest.mark.asyncio
async def test_delete_comment_already_deleted(async_client: AsyncClient, setup_test_comment):
    """
    Teste la suppression d'un commentaire déjà supprimé.
    """
    comment_id = setup_test_comment["id"]
    # Supprimer une première fois
    first_delete_response = await async_client.delete(f"/comments/delete/{comment_id}")
    assert first_delete_response.status_code == 200

    # Tenter de supprimer une deuxième fois
    second_delete_response = await async_client.delete(f"/comments/delete/{comment_id}")
    assert second_delete_response.status_code == 404 # Si NotFoundException est convertie en InternalServerError
    data = second_delete_response.json()
    assert data["success"] is False
    assert "Commentaire déjà supprimé" in data["error"]
