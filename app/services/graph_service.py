import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import Nodes, GraphData
from app.schemas.GraphData import Edge, Position
from app.repositories.graph_repository import GraphRepository

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service pour récupérer et construire le graphe des concepts.
    Optimisé avec SQLAlchemy 2.0 ORM et Eager Loading pour éviter le problème N+1.
    """

    def __init__(self, db: AsyncSession):
        self.repo = GraphRepository(db)

    async def get_graph(self) -> GraphData:
        logger.info("Début de l'extraction du graphe via SQLAlchemy ORM")

        concepts = await self.repo.get_all_concepts_for_graph()

        nodes = []
        edges = []

        for concept in concepts:
            # Construction du dictionnaire des positions
            pos_dict = {}
            for pos in concept.positions:
                pos_dict[pos.vue.value if hasattr(pos.vue, "value") else str(pos.vue)] = Position(
                    x=pos.x, y=pos.y, z=pos.z
                )

            # Calcul de l'année et de l'époque
            annee = None
            epoque = None
            if concept.mathematicien:
                epoque = concept.mathematicien.epoque
                if concept.mathematicien.date_deces:
                    annee = concept.mathematicien.date_deces.year
                elif concept.mathematicien.date_naissance:
                    annee = concept.mathematicien.date_naissance.year + 40

            # Extraction du nœud au format attendu
            nodes.append(
                Nodes(
                    id=concept.id,
                    nom=concept.nom,
                    enonce=concept.enonce,
                    typeMath=concept.type.type if concept.type else None,
                    domaine=concept.category.nom if concept.category else "Non classé",
                    annee=annee,
                    epoque=epoque,
                    position=pos_dict,
                )
            )

            # Construction des arêtes à partir des relations sortantes (source -> cible)
            for rel in concept.outgoing_relations:
                edges.append(
                    Edge(
                        start=int(rel.concept_source) if rel.concept_source else 0,
                        end=int(rel.concept_cible) if rel.concept_cible else 0,
                        type=rel.type_relation,
                    )
                )

        logger.info(f"Graphe extrait avec succès : {len(nodes)} noeuds, {len(edges)} arêtes")

        # Retourne les données sous forme de dictionnaire compatible avec le schéma Pydantic GraphData
        return GraphData(nodes=nodes, edges=edges)
