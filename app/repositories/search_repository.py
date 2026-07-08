from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, literal, union_all, func, or_
from app.db.models import Concept, Mathematicien, Category
from app.schemas.search import SearchFilters


class SearchRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def global_quick_search(self, search_pattern: str, limit: int, query_embedding: list[float] | None = None):
        stmt_concepts = (
            select(Concept.id, Concept.nom, literal("concept").label("entity_type"))
            .where(Concept.nom.ilike(search_pattern))
            .limit(limit)
        )

        stmt_maths = (
            select(Mathematicien.id, Mathematicien.nom, literal("mathematicien").label("entity_type"))
            .where(Mathematicien.nom.ilike(search_pattern))
            .limit(limit)
        )

        stmt_categories = (
            select(Category.id, Category.nom, literal("category").label("entity_type"))
            .where(Category.nom.ilike(search_pattern))
            .limit(limit)
        )

        union_stmt = union_all(stmt_concepts, stmt_maths, stmt_categories).order_by("nom").limit(limit * 2)

        results = list((await self.db.execute(union_stmt)).all())

        # Si on a un embedding et qu'on a peu de résultats textuels stricts, on fait une recherche sémantique
        if query_embedding:
            existing_ids = {r.id for r in results if r.entity_type == "concept"}
            semantic_limit = limit - len(results) if len(results) < limit else 3
            if semantic_limit > 0:
                stmt_semantic = select(Concept.id, Concept.nom, literal("concept").label("entity_type")).where(
                    Concept.embedding.is_not(None)
                )
                if existing_ids:
                    stmt_semantic = stmt_semantic.where(Concept.id.not_in(existing_ids))

                # Tri par similarité cosinus <=>
                stmt_semantic = stmt_semantic.order_by(Concept.embedding.cosine_distance(query_embedding)).limit(
                    semantic_limit
                )
                semantic_results = (await self.db.execute(stmt_semantic)).all()
                results.extend(semantic_results)

        return results

    async def search_concepts(self, search_term: str, pattern: str, filters: SearchFilters):
        ts_vector = func.to_tsvector("french", Concept.nom + " " + Concept.enonce)
        ts_query = func.plainto_tsquery("french", search_term)

        conditions = [or_(Concept.nom.ilike(pattern), ts_vector.op("@@")(ts_query))]

        if filters.verifiedOnly:
            conditions.append(Concept.verification.is_(True))
        if filters.categorie_id:
            conditions.append(Concept.categorie_id == filters.categorie_id)
        if filters.type_id:
            conditions.append(Concept.type_id == filters.type_id)
        if filters.mathematicien_id:
            conditions.append(Concept.mathematicien_id == filters.mathematicien_id)
        if filters.date_start:
            conditions.append(Concept.date_modification >= filters.date_start)
        if filters.date_end:
            conditions.append(Concept.date_modification <= filters.date_end)

        stmt = (
            select(Concept.id, Concept.nom, Concept.enonce.label("extrait"), literal("concept").label("entity_type"))
            .where(*conditions)
            .limit(50)
        )

        result = await self.db.execute(stmt)
        return result.all()

    async def search_maths(self, pattern: str):
        stmt = (
            select(
                Mathematicien.id,
                Mathematicien.nom,
                Mathematicien.biographie.label("extrait"),
                literal("mathematicien").label("entity_type"),
            )
            .where(Mathematicien.nom.ilike(pattern))
            .limit(50)
        )

        result = await self.db.execute(stmt)
        return result.all()

    async def search_categories(self, pattern: str):
        stmt = (
            select(
                Category.id,
                Category.nom,
                Category.description.label("extrait"),
                literal("category").label("entity_type"),
            )
            .where(Category.nom.ilike(pattern))
            .limit(50)
        )

        result = await self.db.execute(stmt)
        return result.all()
