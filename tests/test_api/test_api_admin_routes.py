import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Type
from tests.utils import create_headers_token


@pytest.mark.asyncio
async def test_get_stats(
    async_client: AsyncClient,
    setup_test_user,
    setup_test_concept,
    setup_test_categorie,
    setup_test_mathematicien,
    setup_user_token_admin
):
    """
    Test la route /admin/stats pour s'assurer qu'elle retourne les statistiques correctes.
    """
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get("/admin/stats", headers=headers)
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


@pytest.mark.asyncio
async def test_get_users_admin_route(async_client: AsyncClient, setup_test_user, setup_user_token_admin):
    """
    Test la route /admin/users pour s'assurer qu'elle retourne une liste d'utilisateurs.
    """
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.get("/admin/users", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    users = data["data"]

    assert isinstance(users, list)
    assert len(users) >= 1

    # Vérifie si l'utilisateur de test est présent dans la liste retournée
    found_user = False
    for user in users:
        if user.get("email") == setup_test_user["email"]:
            found_user = True
            assert user.get("username") == setup_test_user["username"]
            assert user.get("role") == setup_test_user["role"]
            assert user.get("is_active") == setup_test_user["is_active"]
            break
    assert found_user, "L'utilisateur de test n'a pas été trouvé dans la réponse de /admin/users."


@pytest.mark.asyncio
async def test_get_concepts_admin_route(db_session: AsyncSession, async_client: AsyncClient, setup_test_concept, setup_user_token_admin):
    """
    Test la route /admin/contents pour s'assurer qu'elle retourne une liste de concepts avec des détails d'administration.
    """
    headers = create_headers_token(setup_user_token_admin)

    response = await async_client.get("/admin/contents", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    concepts = data["data"]

    assert isinstance(concepts, list)
    assert len(concepts) >= 1

    # Vérifie si le concept de test est présent dans la liste retournée
    found_concept = False
    for concept in concepts:
        if concept.get("nom") == setup_test_concept["nom"]:
            found_concept = True
            # On vérifie le type via SQLAlchemy
            query = select(Type).where(Type.type == concept.get("type"))
            result = await db_session.execute(query)
            type_obj = result.scalars().first()
            assert type_obj is not None
            assert type_obj.id == setup_test_concept["type_id"]
            break
    assert found_concept, "Le concept de test n'a pas été trouvé dans la réponse de /admin/contents."


@pytest.mark.asyncio
async def test_recalculate_graph_layout(
    db_session: AsyncSession,
    async_client: AsyncClient,
    setup_test_concept,
    setup_user_token_admin
):
    """
    Test la route POST /admin/recalculate-graph pour s'assurer qu'elle calcule
    et sauvegarde bien les 4 dispositions physiques, grille, arbre et timeline.
    """
    headers = create_headers_token(setup_user_token_admin)
    response = await async_client.post("/admin/recalculate-graph", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert data["data"] == "Graphe recalculé avec succès"
    
    # On vérifie en base que les positions ont bien été générées pour le concept
    from app.db.models import Position
    stmt = select(Position).where(Position.concept_id == setup_test_concept["id"])
    result = await db_session.execute(stmt)
    positions = result.scalars().all()
    
    # Il doit y avoir les 4 vues calculées : grille, physique, arbre, timeline
    vues = [pos.vue for pos in positions]
    assert "grille" in vues
    assert "physique" in vues
    assert "arbre" in vues
    assert "timeline" in vues

