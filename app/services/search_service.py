import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.search_repository import SearchRepository
from app.schemas.search import SearchFilters
from app.services.embedding_service import embedding_service

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: AsyncSession):
        self.repo = SearchRepository(db)

    async def global_quick_search(self, query: str, limit: int = 5) -> list[dict]:
        """Cherche un terme dans les concepts, mathématiciens et catégories."""
        search_pattern = f"%{query}%"
        # Générer l'embedding pour la recherche sémantique
        query_embedding = embedding_service.get_embedding(query)

        rows = await self.repo.global_quick_search(search_pattern, limit, query_embedding)
        return [{"id": r.id, "nom": r.nom, "entity_type": r.entity_type} for r in rows]

    async def advanced_search(self, search_term: str, filters: SearchFilters):
        search_pattern = f"%{search_term}%"
        results = []

        if filters.concept:
            results.extend(await self._search_concepts(search_term, search_pattern, filters))
        if filters.mathematicien:
            results.extend(await self._search_maths(search_pattern))
        if filters.category:
            results.extend(await self._search_categories(search_pattern))

        return results

    async def _search_concepts(self, search_term: str, pattern: str, filters: SearchFilters):
        rows = await self.repo.search_concepts(search_term, pattern, filters)
        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type,
            }
            for r in rows
        ]

    async def _search_maths(self, pattern: str):
        rows = await self.repo.search_maths(pattern)
        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type,
            }
            for r in rows
        ]

    async def _search_categories(self, pattern: str):
        rows = await self.repo.search_categories(pattern)
        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type,
            }
            for r in rows
        ]
