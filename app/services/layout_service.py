import math
import logging
import networkx as nx
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.exceptions import InternalServerError
from app.core.redis_client import redis_db
from app.db.models import Concept, Relation, Position

logger = logging.getLogger(__name__)


class LayoutService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def recalculate_positions(self):
        logger.info("Début du calcul des layouts (physique, grille, arbre, et timeline)...")

        try:
            # 1. Récupération des concepts avec leur mathématicien associé (pour les dates)
            query_concepts = (
                select(Concept)
                .options(joinedload(Concept.mathematicien))
                .order_by(Concept.id)
            )
            result_concepts = await self.db.execute(query_concepts)
            concepts = list(result_concepts.scalars().all())
            concept_ids = [c.id for c in concepts]

            # 2. Récupération des relations pour la structure des graphes
            query_edges = select(Relation.concept_source, Relation.concept_cible)
            result_edges = await self.db.execute(query_edges)
            edges = result_edges.all()

            if not concepts:
                logger.warning("Aucun concept trouvé, calcul annulé.")
                return

            new_positions = []

            # ==========================================
            # 3. CALCUL DU LAYOUT PHYSIQUE (Force-Directed)
            # ==========================================
            G = nx.Graph()
            G.add_nodes_from(concept_ids)
            G.add_edges_from([(e.concept_source, e.concept_cible) for e in edges])

            pos_physique = nx.spring_layout(G, dim=3, scale=30.0, iterations=100)

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

            # ==========================================
            # 4. CALCUL DU LAYOUT GRILLE 3D
            # ==========================================
            n_nodes = len(concept_ids)
            side = math.ceil(n_nodes ** (1 / 3.0))  # Taille d'un côté du cube
            spacing = 6.0  # Espacement entre chaque sphère

            for i, node_id in enumerate(concept_ids):
                x_idx = i % side
                y_idx = (i // side) % side
                z_idx = i // (side * side)

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
            # 5. CALCUL DU LAYOUT ARBRE HIERARCHIQUE
            # ==========================================
            # DAG : Axiomes (niveau 0) en bas, lemmes/théorèmes en haut (Y croissant)
            levels = {c.id: 0 for c in concepts}
            
            # Algorithme de relaxation simple pour assigner les niveaux hiérarchiques (robuste aux cycles)
            for _ in range(50):
                changed = False
                for edge in edges:
                    u = edge.concept_source
                    v = edge.concept_cible
                    if u in levels and v in levels:
                        if levels[v] < levels[u] + 1:
                            levels[v] = levels[u] + 1
                            changed = True
                if not changed:
                    break

            # Grouper les nœuds par niveau
            level_nodes = {}
            for c_id, lvl in levels.items():
                level_nodes.setdefault(lvl, []).append(c_id)

            spacing_y = 10.0  # Espacement vertical
            for lvl, node_list in level_nodes.items():
                n = len(node_list)
                y = float(lvl * spacing_y)  # Les axiomes (niveau 0) restent à y=0, les théorèmes montent

                if n == 1:
                    new_positions.append(
                        Position(concept_id=node_list[0], vue='arbre', x=0.0, y=y, z=0.0)
                    )
                else:
                    # Distribution circulaire sur le plan X-Z pour chaque couche
                    radius = max(4.0, math.sqrt(n) * 3.5)
                    for idx, node_id in enumerate(node_list):
                        angle = (2 * math.pi * idx) / n
                        x = radius * math.cos(angle)
                        z = radius * math.sin(angle)
                        new_positions.append(
                            Position(concept_id=node_id, vue='arbre', x=float(x), y=y, z=float(z))
                        )

            # ==========================================
            # 6. CALCUL DU LAYOUT CHRONOLOGIQUE (Timeline)
            # ==========================================
            # Axe temporel sur Z
            years_with_data = []
            for c in concepts:
                if c.mathematicien and c.mathematicien.date_naissance:
                    years_with_data.append(c.mathematicien.date_naissance.year)
            
            min_year = min(years_with_data) if years_with_data else 1500
            max_year = max(years_with_data) if years_with_data else 2000
            default_year = int(sum(years_with_data) / len(years_with_data)) if years_with_data else 1800

            # Grouper par décennie pour tasser les concepts proches sur le même Z
            time_groups = {}
            for c in concepts:
                year = c.mathematicien.date_naissance.year if (c.mathematicien and c.mathematicien.date_naissance) else default_year
                decade = (year // 10) * 10
                time_groups.setdefault(decade, []).append(c.id)

            year_span = (max_year - min_year) if (max_year - min_year) > 0 else 100

            for decade, node_list in time_groups.items():
                # Normalisation de Z entre -35 et +35
                z = float(((decade - min_year) / year_span) * 70.0 - 35.0)
                n = len(node_list)

                if n == 1:
                    new_positions.append(
                        Position(concept_id=node_list[0], vue='timeline', x=0.0, y=0.0, z=z)
                    )
                else:
                    # Distribution circulaire sur le plan X-Y pour éviter les superpositions à la même date
                    radius = max(3.0, math.sqrt(n) * 2.5)
                    for idx, node_id in enumerate(node_list):
                        angle = (2 * math.pi * idx) / n
                        x = radius * math.cos(angle)
                        y = radius * math.sin(angle)
                        new_positions.append(
                            Position(concept_id=node_id, vue='timeline', x=float(x), y=float(y), z=z)
                        )

            # ==========================================
            # 7. SAUVEGARDE EN BASE DE DONNÉES
            # ==========================================
            await self.db.execute(
                delete(Position).where(Position.vue.in_(['physique', 'grille', 'arbre', 'timeline']))
            )

            self.db.add_all(new_positions)
            await self.db.flush()
            await redis_db.delete("mathgraph:data")

            logger.info("Layouts 'physique', 'grille', 'arbre', et 'timeline' recalculés et sauvegardés avec succès !")

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des positions : {e}")
            raise InternalServerError("Erreur lors de la mise à jour des positions physiques et structurées.")