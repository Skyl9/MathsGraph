from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, delete, or_
from sqlalchemy.orm import selectinload, joinedload
from app.db.models import (
    Concept,
    ConceptVersion,
    Relation,
    Alias,
    Source,
    ForeignName,
    Mathematicien,
    Category,
    Type,
    User,
)


class ConceptRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_concept_info(self, concept_id: int):
        query = (
            select(Concept)
            .where(Concept.id == concept_id)
            .options(
                joinedload(Concept.type),
                joinedload(Concept.mathematicien),
                joinedload(Concept.category),
                selectinload(Concept.aliases),
                selectinload(Concept.sources),
                selectinload(Concept.tags),
                selectinload(Concept.foreign_names),
                selectinload(Concept.outgoing_relations).joinedload(Relation.target_concept),
                selectinload(Concept.incoming_relations).joinedload(Relation.source_concept),
            )
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_version_for_rollback(self, concept_id: int, version_number: int, field_modified: str):
        query = select(ConceptVersion).where(
            ConceptVersion.concept_id == concept_id,
            ConceptVersion.version_number == version_number,
            ConceptVersion.field_modified == field_modified,
        )
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_math_dict(self, math_ids: set):
        res_math = await self.db.execute(select(Mathematicien).where(Mathematicien.id.in_(math_ids)))
        return {m.id: m.nom for m in res_math.scalars()}

    async def get_cat_dict(self, cat_ids: set):
        res_cat = await self.db.execute(select(Category).where(Category.id.in_(cat_ids)))
        return {c.id: c.nom for c in res_cat.scalars()}

    async def get_type_dict(self, type_ids: set):
        res_type = await self.db.execute(select(Type).where(Type.id.in_(type_ids)))
        return {t.id: t.type for t in res_type.scalars()}

    async def get_concept_dict(self, concept_ids: set):
        res_concept = await self.db.execute(select(Concept.id, Concept.nom).where(Concept.id.in_(concept_ids)))
        return {row.id: row.nom for row in res_concept.all()}

    async def get_concept_versions(self, concept_id: int):
        query = (
            select(ConceptVersion)
            .options(joinedload(ConceptVersion.modifier))
            .where(ConceptVersion.concept_id == concept_id)
            .order_by(desc(ConceptVersion.version_number))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_concepts_name(self):
        query = select(Concept.id, Concept.nom)
        result = await self.db.execute(query)
        return result.all()

    async def get_type_by_id(self, type_id: int):
        return await self.db.get(Type, type_id)

    async def get_category_by_id(self, cat_id: int):
        return await self.db.get(Category, cat_id)

    async def get_mathematicien_by_id(self, math_id: int):
        return await self.db.get(Mathematicien, math_id)

    async def get_concept_by_id(self, concept_id: int):
        return await self.db.get(Concept, concept_id)

    async def get_type_id_by_name(self, name: str):
        query = select(Type.id).where(Type.type == name)
        return await self.db.scalar(query)

    async def get_category_id_by_name(self, name: str):
        query = select(Category.id).where(Category.nom == name)
        return await self.db.scalar(query)

    async def get_mathematicien_id_by_name(self, name: str):
        query = select(Mathematicien.id).where(Mathematicien.nom == name)
        return await self.db.scalar(query)

    async def get_concept_relations(self, concept_id: int):
        query = select(Relation).where(or_(Relation.concept_source == concept_id, Relation.concept_cible == concept_id))
        res = await self.db.execute(query)
        return res.scalars().all()

    async def delete_concept_relations(self, concept_id: int):
        await self.db.execute(
            delete(Relation).where(or_(Relation.concept_source == concept_id, Relation.concept_cible == concept_id))
        )

    async def get_concept_sources(self, concept_id: int):
        query = select(Source).join(Concept.sources).where(Concept.id == concept_id)
        res = await self.db.execute(query)
        return res.scalars().all()

    async def get_source_by_id(self, source_id: int):
        return await self.db.get(Source, source_id)

    async def get_concept_aliases(self, concept_id: int):
        query = select(Alias).where(Alias.concept_id == concept_id)
        res = await self.db.execute(query)
        return res.scalars().all()

    async def delete_concept_aliases(self, concept_id: int):
        await self.db.execute(delete(Alias).where(Alias.concept_id == concept_id))

    async def get_concept_foreign_names(self, concept_id: int):
        query = select(ForeignName).where(ForeignName.concept_id == concept_id)
        res = await self.db.execute(query)
        return res.scalars().all()

    async def delete_concept_foreign_names(self, concept_id: int):
        await self.db.execute(delete(ForeignName).where(ForeignName.concept_id == concept_id))

    async def get_editable_fields_options(self):
        types = (await self.db.execute(select(Type.type).distinct())).scalars().all()
        categories = (await self.db.execute(select(Category.nom).distinct())).scalars().all()
        mathematiciens = (await self.db.execute(select(Mathematicien.nom).distinct())).scalars().all()
        return {"mathematicien": list(mathematiciens), "categorie": list(categories), "type": list(types)}

    async def get_recent_history(self, limit: int):
        query = (
            select(ConceptVersion)
            .options(joinedload(ConceptVersion.modifier), joinedload(ConceptVersion.concept))
            .order_by(desc(ConceptVersion.modified_at))
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_concept_id_by_name(self, name: str):
        query = select(Concept.id).where(Concept.nom == name)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_user_id_by_username(self, username: str):
        query = select(User.id).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_next_version_number(self, concept_id: int, field_modified: str):
        await self.db.execute(select(Concept.id).where(Concept.id == concept_id).with_for_update())

        query_v = select(func.coalesce(func.max(ConceptVersion.version_number), 0) + 1).where(
            ConceptVersion.concept_id == concept_id, ConceptVersion.field_modified == field_modified
        )
        return await self.db.scalar(query_v)

    async def get_next_global_version(self, concept_id: int):
        await self.db.execute(select(Concept.id).where(Concept.id == concept_id).with_for_update())

        query_gv = select(func.coalesce(func.max(ConceptVersion.global_version), 0) + 1).where(
            ConceptVersion.concept_id == concept_id
        )
        return await self.db.scalar(query_gv)

    async def add(self, entity):
        self.db.add(entity)

    async def flush(self):
        await self.db.flush()

    async def commit(self):
        await self.db.commit()
