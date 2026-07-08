import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Concept, Category
from app.services.embedding_service import embedding_service


@pytest.mark.asyncio
async def test_get_wanted_concepts_empty(async_client: AsyncClient, db_session: AsyncSession):
    response = await async_client.get("/concepts/wanted")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["error"] is None
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
async def test_get_wanted_concepts_with_data(async_client: AsyncClient, db_session: AsyncSession):
    # Créer une catégorie
    cat = Category(nom="Topologie")
    db_session.add(cat)
    await db_session.flush()

    # Créer un concept "wanted" (pas de démonstration, pas de sources)
    embedding = embedding_service.get_embedding("Concept test voulu")
    wanted_concept = Concept(
        nom="Concept test voulu",
        enonce="Ceci est un test",
        demonstration=None,
        categorie_id=cat.id,
        embedding=embedding,
    )
    db_session.add(wanted_concept)
    await db_session.flush()

    response = await async_client.get("/concepts/wanted")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) >= 1

    # Vérifier que notre concept est bien remonté et possède les bons champs manquants
    test_concept = next((c for c in data["data"] if c["nom"] == "Concept test voulu"), None)
    assert test_concept is not None
    assert test_concept["categorie"] == "Topologie"
    assert "demonstration" in test_concept["missing_fields"]
    assert "sources" in test_concept["missing_fields"]
