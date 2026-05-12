import logging
from typing import List

from psycopg import AsyncConnection

from app.schemas import Nodes, GraphData
from app.schemas.GraphData import Edge

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service pour récupérer et construire le graphe des concepts.

    Responsabilités :
      - Extraire les nœuds (concepts) avec leurs attributs (id, nom, type).
      - Extraire les positions associées aux vues 'grille' et 'arbre'.
      - Assembler et renvoyer une structure au format { "nodes": [...], "edges": [] }.
    """

    def __init__(self, db: AsyncConnection):
        """
               Initialise le service avec une connexion asynchrone à la base de données.

               Args:
                   db (AsyncConnection): connexion PostgreSQL asynchrone.
               """

        self.db = db

    # TODO Fractionner le code pour obtenir les noeuds/arrete et les positions
    async def get_graph(self) -> GraphData:
        """
               Récupère la représentation du graphe des concepts depuis la base.

               Effectue deux requêtes :
                 1. Sélection des concepts (id, nom, type).
                 2. Sélection des positions (concept_id, vue, x, y, z).

               Construit ensuite :
                 - un dictionnaire `positions_dict` indexé par concept_id,
                 - une liste de nœuds enrichis de leurs coordonnées,
                 - un tableau d'arêtes (vide pour l'instant).

               Returns:
                   dict[str, list]:
                       {
                         "nodes": [
                           {
                             "id": int,
                             "nom": str,
                             "typeMath": str | None,
                             "position": {
                               "grille": {"x": float, "y": float, "z": float},
                               "arbre": {"x": float, "y": float, "z": float}
                             }
                           }, ...
                         ],
                         "edges": []
                       }

               Raises:
                   InternalServerError: en cas d'erreur inattendue lors de l'accès ou du traitement des données.
               """

        logger.info("Début de l'extraction du graphe")
        async with self.db.cursor() as cur:

            # Récupérer les informations de base des concepts
            await cur.execute(
                "SELECT c.id, c.nom, t.type FROM concepts c LEFT JOIN type t on type_id = t.id ORDER BY id ;")
            concepts = await cur.fetchall()

            # Récupérer les positions des concepts
            await cur.execute("SELECT concept_id, vue, x, y, z FROM positions WHERE vue IN ('grille', 'arbre');")
            positions = await cur.fetchall()

            await cur.execute("SELECT concept_source, concept_cible, type_relation FROM relations;")
            relations = await cur.fetchall()

        positions_dict = {}
        for concept_id, vue, x, y, z in positions:
            if concept_id not in positions_dict:
                positions_dict[concept_id] = {}
            positions_dict[concept_id][vue] = {"x": x, "y": y, "z": z}

        # Construire le dictionnaire final
        nodes: List[Nodes] = []
        for concept_id, nom, concept_type in concepts:
            nodes.append({
                "id": concept_id,
                "nom": nom,
                "typeMath": concept_type,
                "position": positions_dict.get(concept_id, {})
            })
        edges: List[Edge] = []
        for start_id, end_id, type_relation in relations:
            edges.append({
                "start": start_id,
                "end": end_id,
                "type": type_relation
            })

        logger.info(f"Graphe extrait avec succès : {len(nodes)} noeuds, {len(edges)} arêtes")

        return {'nodes': nodes, 'edges': edges}
