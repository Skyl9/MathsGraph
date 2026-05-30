import logging
from sqlalchemy import select, literal, union_all, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

# N'oublie pas d'importer tes modèles
from app.db.models import Concept, Mathematicien, Category

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def global_quick_search(self, query: str, limit: int = 5) -> list[dict]:
        """Cherche un terme dans les concepts, mathématiciens et catégories."""
        search_pattern = f"%{query}%"

        # 1. Préparation des 3 sous-requêtes
        stmt_concepts = select(
            Concept.id,
            Concept.nom,
            literal("concept").label("entity_type")
        ).where(Concept.nom.ilike(search_pattern)).limit(limit)

        stmt_maths = select(
            Mathematicien.id,
            Mathematicien.nom,
            literal("mathematicien").label("entity_type")
        ).where(Mathematicien.nom.ilike(search_pattern)).limit(limit)

        stmt_categories = select(
            Category.id,
            Category.nom,
            literal("category").label("entity_type")
        ).where(Category.nom.ilike(search_pattern)).limit(limit)

        # 2. On les unit (UNION ALL) et on ordonne le résultat final
        union_stmt = union_all(stmt_concepts, stmt_maths, stmt_categories) \
            .order_by("nom") \
            .limit(limit * 2)

        # 3. Exécution
        result = await self.db.execute(union_stmt)
        rows = result.all()

        return [
            {"id": r.id, "nom": r.nom, "entity_type": r.entity_type}
            for r in rows
        ]

    async def advanced_search(self, search_term: str, filters: dict):
        search_pattern = f"%{search_term}%"
        results = []

        # pour respecter le fonctionnement de la session SQLAlchemy
        if filters.get("concept"):
            results.extend(await self._search_concepts(search_term, search_pattern, filters))
        if filters.get("mathematicien"):
            results.extend(await self._search_maths(search_pattern))
        if filters.get("category"):
            results.extend(await self._search_categories(search_pattern))

        return results

    async def _search_concepts(self, search_term: str, pattern: str, filters: dict):
        ts_vector = func.to_tsvector('french', Concept.nom + ' ' + Concept.enonce)
        ts_query = func.plainto_tsquery('french', search_term)

        stmt = select(
            Concept.id,
            Concept.nom,
            Concept.enonce.label("extrait"),
            literal("concept").label("entity_type")
        ).where(
            or_(
                Concept.nom.ilike(pattern),
                ts_vector.op('@@')(ts_query)
            )
        ).limit(50)

        result = await self.db.execute(stmt)

        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type
            } for r in result.all()
        ]

    async def _search_maths(self, pattern: str):
        stmt = select(
            Mathematicien.id,
            Mathematicien.nom,
            Mathematicien.biographie.label("extrait"),
            literal("mathematicien").label("entity_type")
        ).where(Mathematicien.nom.ilike(pattern)).limit(50)

        result = await self.db.execute(stmt)

        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type
            } for r in result.all()
        ]

    async def _search_categories(self, pattern: str):
        stmt = select(
            Category.id,
            Category.nom,
            Category.description.label("extrait"),
            literal("category").label("entity_type")
        ).where(Category.nom.ilike(pattern)).limit(50)

        result = await self.db.execute(stmt)

        return [
            {
                "id": r.id,
                "nom": r.nom,
                "extrait": (r.extrait[:100] + "...") if r.extrait else "",
                "entity_type": r.entity_type
            } for r in result.all()
        ]