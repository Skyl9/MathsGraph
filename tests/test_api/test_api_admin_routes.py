import pytest
from httpx import AsyncClient
import psycopg

@pytest.mark.asyncio
async def test_get_stats(
    async_client: AsyncClient,
    setup_test_user,
    setup_test_concept,
    setup_test_categorie,
    setup_test_mathematicien
):
    """
    Test la route /getAlldatabaseInfo pour s'assurer qu'elle retourne les statistiques correctes.
    """
    response = await async_client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    stats = data["data"]

    # Vérifie les clés attendues retournées par admin_service.py's get_stats
    expected_keys = ["users", "favorites", "concepts", "categories", "mathematicien"]
    for key in expected_keys:
        assert key in stats, f"La clé '{key}' n'a pas été trouvée dans la réponse des statistiques."

    # Vérifie les décomptes (au moins 1 pour les fixtures de configuration)
    assert stats["users"] >= 1
    assert stats["concepts"] >= 1
    assert stats["categories"] >= 1
    assert stats["mathematicien"] >= 1
    # Le nombre de favoris peut être 0 si aucun favori n'est explicitement configuré.


@pytest.mark.asyncio
async def test_get_users_admin_route(async_client: AsyncClient, setup_test_user):
    """
    Test la route /admin/users pour s'assurer qu'elle retourne une liste d'utilisateurs.
    Ce test suppose que l'authentification admin n'est pas strictement requise pour la configuration,
    ou qu'elle est gérée par async_client.
    """
    response = await async_client.get("/admin/users")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    users = data["data"]

    assert isinstance(users, list)
    assert len(users) >= 1  # Au moins l'utilisateur créé par setup_test_user

    # Vérifie si l'utilisateur de test est présent dans la liste retournée et si ses détails correspondent
    found_user = False
    for user in users:
        if user.get("email") == setup_test_user["email"]:
            found_user = True
            assert user.get("username") == setup_test_user["username"]
            assert user.get("role") == setup_test_user["role"]
            assert user.get("is_active") == setup_test_user["is_active"]
            # `created_at` peut avoir des différences de fuseau horaire, nous ignorons donc l'égalité directe pour l'instant
            break
    assert found_user, "L'utilisateur de test n'a pas été trouvé dans la réponse de /admin/users."


@pytest.mark.asyncio
async def test_get_concepts_admin_route(transaction,async_client: AsyncClient, setup_test_concept):
    """
    Test la route /admin/concepts pour s'assurer qu'elle retourne une liste de concepts avec des détails d'administration.
    Ce test suppose que l'authentification admin n'est pas strictement requise pour la configuration,
    ou qu'elle est gérée par async_client.
    """
    response = await async_client.get("/admin/contents")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    concepts = data["data"]

    assert isinstance(concepts, list)
    assert len(concepts) >= 1  # Au moins le concept créé par setup_test_concept

    # Vérifie si le concept de test est présent dans la liste retournée et si ses détails correspondent
    found_concept = False
    for concept in concepts:
        async with transaction.connection.cursor() as cur:
            await cur.execute("SELECT id FROM type WHERE type.type = %s", (concept.get("type"),))
            type_id = await cur.fetchone()
            assert type_id is not None
        if concept.get("nom") == setup_test_concept["nom"]:
            found_concept = True
            assert type_id[0] == setup_test_concept["type_id"]
            break
    assert found_concept, "Le concept de test n'a pas été trouvé dans la réponse de /admin/concepts."
