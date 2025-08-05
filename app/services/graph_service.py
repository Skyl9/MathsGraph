from psycopg import AsyncConnection

from app.schemas import Nodes


class GraphService:
    def __init__(self,db:AsyncConnection):
        self.db = db

    async def get_graph(self) -> Nodes:
        """Récupère les informations des concepts et leurs positions."""
        with self.db.cursor() as cur:

            # Récupérer les informations de base des concepts
            await cur.execute("SELECT c.id, c.nom, t.type FROM concepts c LEFT JOIN type t on type_id = t.id ORDER BY id ;")
            concepts = await cur.fetchall()

            # Récupérer les positions des concepts
            await cur.execute("SELECT concept_id, vue, x, y, z FROM positions WHERE vue IN ('grille', 'arbre');")
            positions = await cur.fetchall()

        positions_dict = {}
        for concept_id, vue, x, y, z in positions:
            if concept_id not in positions_dict:
                positions_dict[concept_id] = {}
            positions_dict[concept_id][vue] = {"x": x, "y": y, "z": z}

        # Construire le dictionnaire final
        result = []
        for concept_id, nom, concept_type in concepts:
            result.append({
                "id": concept_id,
                "nom": nom,
                "typeMath": concept_type,
                "position": positions_dict.get(concept_id, {})
            })

        return {'nodes': result, "edges": []}
            # Créer un dictionnaire de positions par concept_id

