import logging
from typing import List
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.schemas import Nodes, GraphData
from app.schemas.GraphData import Edge
from app.db.models import Concept, Position, Relation, Type

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service pour récupérer et construire le graphe des concepts.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_graph(self) -> GraphData:
        logger.info("Début de l'extraction du graphe")

        # Récupérer les informations de base des concepts avec leur type
        query_concepts = (
            select(Concept)
            .options(joinedload(Concept.type))
            .order_by(Concept.id)
        )
        result_concepts = await self.db.execute(query_concepts)
        concepts = result_concepts.scalars().all()

        # Récupérer les positions des concepts
        query_positions = (
            select(Position)
            .where(Position.vue.in_(['grille', 'arbre', 'physique']))
        )
        result_positions = await self.db.execute(query_positions)
        positions = result_positions.scalars().all()

        # Récupérer les relations
        query_relations = select(Relation)
        result_relations = await self.db.execute(query_relations)
        relations = result_relations.scalars().all()

        # Construire le dictionnaire des positions
        positions_dict = {}
        for pos in positions:
            if pos.concept_id not in positions_dict:
                positions_dict[pos.concept_id] = {}
            positions_dict[pos.concept_id][pos.vue] = {"x": pos.x, "y": pos.y, "z": pos.z}

        # Construire la liste des nœuds
        nodes: List[dict] = []
        for c in concepts:
            nodes.append({
                "id": c.id,
                "nom": c.nom,
                "typeMath": c.type.type if c.type else None,
                "position": positions_dict.get(c.id, {})
            })

        # Construire la liste des arêtes
        edges: List[dict] = []
        for r in relations:
            edges.append({
                "start": r.concept_source,
                "end": r.concept_cible,
                "type": r.type_relation
            })

        logger.info(f"Graphe extrait avec succès : {len(nodes)} noeuds, {len(edges)} arêtes")

        return {'nodes': nodes, 'edges': edges}
