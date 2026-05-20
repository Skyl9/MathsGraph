import math
import logging
import networkx as nx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InternalServerError
from app.db.models import Concept, Relation, Position

logger = logging.getLogger(__name__)


class LayoutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recalculate_positions(self):
        logger.info("Début du calcul des layouts (physique et grille)...")

        try:
            # 1. Récupération des nœuds
            query_nodes = select(Concept.id).order_by(Concept.id)
            result_nodes = await self.db.execute(query_nodes)
            node_ids = list(result_nodes.scalars().all())

            # 2. Récupération des relations (Sans scalars() car on veut deux colonnes !)
            query_edges = select(Relation.concept_source, Relation.concept_cible)
            result_edges = await self.db.execute(query_edges)
            edges = result_edges.all()

            if not node_ids:
                logger.warning("Aucun nœud trouvé, calcul annulé.")
                return

            # ==========================================
            # 3. CALCUL DU LAYOUT PHYSIQUE (Force-Directed)
            # ==========================================
            G = nx.Graph()
            G.add_nodes_from(node_ids)
            G.add_edges_from([(e.concept_source, e.concept_cible) for e in edges])

            pos_physique = nx.spring_layout(G, dim=3, scale=30.0, iterations=100)

            # ==========================================
            # 4. CALCUL DU LAYOUT GRILLE 3D
            # ==========================================
            n_nodes = len(node_ids)
            side = math.ceil(n_nodes ** (1 / 3.0))  # Taille d'un côté du cube
            spacing = 6.0  # Espacement entre chaque sphère

            # Liste qui va contenir toutes nos nouvelles positions à insérer
            new_positions = []

            # Préparation des positions physiques
            for node_id, coords in pos_physique.items():
                new_positions.append(
                    Position(
                        concept_id=node_id,
                        vue='physique',
                        x=float(coords[0]),
                        y=float(coords[1]),
                        z=float(coords[2])
                    )
                )

            # Préparation des positions de la grille
            for i, node_id in enumerate(node_ids):
                x_idx = i % side
                y_idx = (i // side) % side
                z_idx = i // (side * side)

                # On centre la grille autour du point (0,0,0)
                new_positions.append(
                    Position(
                        concept_id=node_id,
                        vue='grille',
                        x=float((x_idx - side / 2) * spacing),
                        y=float((y_idx - side / 2) * spacing),
                        z=float((z_idx - side / 2) * spacing)
                    )
                )

            # ==========================================
            # 5. SAUVEGARDE EN BASE DE DONNÉES
            # ==========================================
            await self.db.execute(
                delete(Position).where(Position.vue.in_(['physique', 'grille']))
            )

            self.db.add_all(new_positions)
            await self.db.flush()

            logger.info("Layouts 'physique' et 'grille' recalculés et sauvegardés avec succès !")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des positions : {e}")
            raise InternalServerError("Erreur lors de la mise à jour des positions physiques.")