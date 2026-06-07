from app.schemas.enums import VueLayout

import math
import logging
import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InternalServerError
from app.core.redis_client import redis_db
from app.db.models import Position
from app.repositories.layout_repository import LayoutRepository

logger = logging.getLogger(__name__)


class LayoutService:
    def __init__(self, db: AsyncSession):
        self.repo = LayoutRepository(db)

    async def recalculate_positions(self):
        logger.info("Début du calcul des layouts (physique, grille, arbre, et timeline)...")

        try:
            # 1. Récupération des concepts avec leur mathématicien associé (pour les dates)
            concepts = await self.repo.get_all_concepts_with_mathematicien()
            concept_ids = [c.id for c in concepts]

            # 2. Récupération des relations pour la structure des graphes
            edges = await self.repo.get_all_edges()

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
                        vue=VueLayout.physique,
                        x=float(coords[0]),
                        y=float(coords[1]),
                        z=float(coords[2]),
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
                        vue=VueLayout.grille,
                        x=float((x_idx - side / 2) * spacing),
                        y=float((y_idx - side / 2) * spacing),
                        z=float((z_idx - side / 2) * spacing),
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

            # Calculer un layout 2D pour organiser les branches spatialement sans qu'elles se croisent trop
            pos_2d = nx.spring_layout(G, dim=2, scale=40.0, iterations=100)

            spacing_y = 15.0  # Espacement vertical
            for node_id, coords in pos_2d.items():
                lvl = levels.get(node_id, 0)
                y = float(lvl * spacing_y)
                x = float(coords[0])
                z = float(coords[1])

                new_positions.append(Position(concept_id=node_id, vue=VueLayout.arbre, x=x, y=y, z=z))

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
                year = (
                    c.mathematicien.date_naissance.year
                    if (c.mathematicien and c.mathematicien.date_naissance)
                    else default_year
                )
                decade = (year // 10) * 10
                time_groups.setdefault(decade, []).append(c.id)

            year_span = (max_year - min_year) if (max_year - min_year) > 0 else 100

            for decade, node_list in time_groups.items():
                # Normalisation de Z entre -35 et +35
                z = float(((decade - min_year) / year_span) * 70.0 - 35.0)
                n = len(node_list)

                if n == 1:
                    new_positions.append(Position(concept_id=node_list[0], vue=VueLayout.timeline, x=0.0, y=0.0, z=z))
                else:
                    # Distribution circulaire sur le plan X-Y pour éviter les superpositions à la même date
                    radius = max(3.0, math.sqrt(n) * 2.5)
                    for idx, node_id in enumerate(node_list):
                        angle = (2 * math.pi * idx) / n
                        x = radius * math.cos(angle)
                        y = radius * math.sin(angle)
                        new_positions.append(
                            Position(concept_id=node_id, vue=VueLayout.timeline, x=float(x), y=float(y), z=z)
                        )

            # ==========================================
            # 7. SAUVEGARDE EN BASE DE DONNÉES
            # ==========================================
            await self.repo.delete_positions_by_views(
                [VueLayout.physique, VueLayout.grille, VueLayout.arbre, VueLayout.timeline]
            )

            self.repo.add_all_positions(new_positions)
            await self.repo.flush()
            await redis_db.delete("mathgraph:data")

            logger.info(
                "Layouts VueLayout.PHYSIQUE, VueLayout.GRILLE, VueLayout.ARBRE, et VueLayout.TIMELINE recalculés et sauvegardés avec succès !"
            )

        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des positions : {e}")
            raise InternalServerError("Erreur lors de la mise à jour des positions physiques et structurées.")
