import logging
from typing import List, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.schemas import Nodes, GraphData
from app.schemas.GraphData import Edge
from app.db.models import Concept, Position, Relation, Type

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service pour récupérer et construire le graphe des concepts.
    Optimisé avec SQLAlchemy 2.0 ORM et Eager Loading pour éviter le problème N+1.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_graph(self) -> GraphData:
        logger.info("Début de l'extraction du graphe via SQLAlchemy ORM")

        # Requête unique ultra-optimisée avec eager loading
        # joinedload pour les relations Many-to-One (Type)
        # selectinload pour les relations One-to-Many (Positions, Relations sortantes)
        stmt = (
            select(Concept)
            .options(
                joinedload(Concept.type),
                selectinload(Concept.positions),
                selectinload(Concept.outgoing_relations)
            )
            .order_by(Concept.id)
        )
        
        result = await self.db.execute(stmt)
        concepts = result.scalars().all()

        nodes = []
        edges = []
        
        for concept in concepts:
            # Construction du dictionnaire des positions
            pos_dict = {}
            for pos in concept.positions:
                pos_dict[pos.vue] = {
                    "x": pos.x,
                    "y": pos.y,
                    "z": pos.z
                }
            
            # Extraction du nœud au format attendu
            nodes.append({
                "id": concept.id,
                "nom": concept.nom,
                "enonce": concept.enonce,
                "typeMath": concept.type.type if concept.type else None,
                "position": pos_dict
            })

            # Construction des arêtes à partir des relations sortantes (source -> cible)
            for rel in concept.outgoing_relations:
                edges.append({
                    "start": rel.concept_source,
                    "end": rel.concept_cible,
                    "type": rel.type_relation
                })

        logger.info(f"Graphe extrait avec succès : {len(nodes)} noeuds, {len(edges)} arêtes")

        # Retourne les données sous forme de dictionnaire compatible avec le schéma Pydantic GraphData
        return {"nodes": nodes, "edges": edges}
