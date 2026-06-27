from app.core.redis_client import invalidate_graph_cache
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, NotFoundException
from app.schemas import CreateRelation
from app.db.models import Relation
from app.repositories.relation_repository import RelationRepository


logger = logging.getLogger(__name__)


class RelationService:
    def __init__(self, db: AsyncSession):
        self.repo = RelationRepository(db)

    async def add_relation(self, data: CreateRelation):
        data_dict = data.model_dump() if isinstance(data, CreateRelation) else data
        val = data_dict["value"]

        # Récupérer les IDs des concepts
        theo1 = await self.repo.get_concept_id_by_name(val["théo1"])
        theo2 = await self.repo.get_concept_id_by_name(val["théo2"])

        if theo1 is None or theo2 is None:
            raise NotFoundException(detail="Concept not found")
        if theo1 == theo2:
            raise ConflictException(detail="Concept cannot be related to itself")

        # Vérifier si la relation existe déjà
        rel_id = await self.repo.get_relation_id(theo1, theo2)
        if rel_id is not None:
            raise ConflictException(detail="Relation already exists")

        new_rel = Relation(
            concept_source=theo1, concept_cible=theo2, type_relation=val["relation"], description=val["desc"]
        )
        await self.repo.add(new_rel)

        # Invalidation du cache Redis global du graphe
        try:
            await invalidate_graph_cache()
        except Exception as e:
            logger.warning(f"Erreur lors de l'invalidation du cache Redis: {e}")
