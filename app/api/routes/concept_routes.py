import psycopg2
from fastapi import APIRouter, HTTPException

from app.db.database import get_db_connection
from app.schemas import CategorieBase
from app.schemas.EditableClass import EditableField
from app.schemas.GraphData import Nodes, GraphData
from app.schemas.concept import ConceptResponse, ConceptName
from app.schemas.mathematicien import MathematicienResponse
from app.schemas.pathcClass import UpdateConceptDict
from app.schemas.response import Response
from typing import List

from app.services.concept_service import ConceptService

#TODO Modifier updateOneCategory pour prendre en compte si utilisateur + historique

router = APIRouter(prefix="", tags=["concepts"])


def get_mathematiciens(conn) -> MathematicienResponse:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM mathematiciens")
        return cur.fetchall()


def get_categories(conn) -> CategorieBase:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM categories")
        return cur.fetchall()


def get_concept_info(concept_id, connection) -> ConceptResponse:
    with connection.cursor() as cursor:
        # Récupérer les informations de base sur le concept
        cursor.execute("""
                       SELECT c.id,
                              c.nom,
                              t.type,
                              c.enonce,
                              c.demonstration,
                              c.verification,
                              c.date_modification,
                              m.id,
                              m.nom,
                              cat.id,
                              cat.nom
                       FROM concepts c
                                LEFT JOIN mathematiciens m ON c.mathematicien_id = m.id
                                LEFT JOIN categories cat ON c.categorie_id = cat.id
                                LEFT JOIN type t ON c.type_id = t.id
                       WHERE c.id = %s
                       ORDER BY c.id ASC
                       """, (concept_id,))
        result = cursor.fetchone()

        if not result:
            return None  # Si le concept n'existe pas

        concept = {
            "id": result[0],
            "nom": result[1],
            "type": result[2],
            "enonce": result[3],
            "demonstration": result[4],
            "verification": result[5],
            "date_modification": result[6],
            "mathematicien": {"id": result[7], "mathematicien": result[8]}
            if result[7] else None,
            "categorie": {"id": result[9], "category": result[10]}
            if result[9] else None,
        }
        print(concept)

        # Récupérer les alias du concept
        cursor.execute("SELECT alias FROM aliases WHERE concept_id = %s", (concept_id,))
        concept["aliases"] = [row[0] for row in cursor.fetchall()]

        # Récupérer les sources liées au concept
        cursor.execute("""
                       SELECT DISTINCT s.id, s.titre, s.auteur, s.annee, s.url, s."type"
                       FROM sources s
                                JOIN concepts_sources cs ON s.id = cs.source_id
                       WHERE cs.concept_id = %s
                       """, (concept_id,))
        concept["sources"] = [
            {
                "id": row[0],
                "titre": row[1],
                "auteur": row[2],
                "annee": row[3],
                "url": row[4],
                "type": row[5],
            } for row in cursor.fetchall()
        ]

        # Récupérer les relations du concept (sources ou cibles)
        cursor.execute("""
                       SELECT r.id,
                              r.concept_source,
                              c_source.nom AS nom_source,
                              r.concept_cible,
                              c_cible.nom  AS nom_cible,
                              r.type_relation,
                              r.description,
                              r.date_relation
                       FROM relations r
                                JOIN concepts c_source ON r.concept_source = c_source.id
                                JOIN concepts c_cible ON r.concept_cible = c_cible.id
                       WHERE concept_source = %s
                          OR concept_cible = %s
                       """, (concept_id, concept_id))
        concept["relations"] = [
            {
                "id": row[0],
                "concept_source": {"id": row[1], "nom": row[2]},
                "concept_cible": {"id": row[3], "nom": row[4]},
                "type_relation": row[5],
                "description": row[6],
            } for row in cursor.fetchall()
        ]
        cursor.execute("""
                       SELECT id, "Nom_francais", "Nom_étranger", langue
                       FROM foreign_name
                       WHERE "Nom_francais" = (SELECT nom FROM concepts WHERE id = %s)

                       """, (concept_id,))
        concept["noms_etrangers"] = [
            {
                "id": row[0],
                "Nom_francais": row[1],
                "Nom_étranger": row[2],
                "langue": row[3],
            } for row in cursor.fetchall()
        ]

        return concept


def get_conceptsAdmin(conn) -> List[ConceptResponse]:
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Récupérer les concepts
        cur.execute("SELECT * FROM concepts ORDER BY id ")
        concepts = cur.fetchall()

        # Récupération des sources liées aux concepts
        cur.execute("""
                    SELECT cs.concept_id, s.*
                    FROM concepts_sources cs
                             JOIN sources s ON cs.source_id = s.id
                    """)
        sources = {}
        for row in cur.fetchall():
            sources.setdefault(row['concept_id'], []).append(dict(row))

        # Récupération des alias
        cur.execute("""
                    SELECT concept_id, alias
                    FROM aliases
                    """)
        aliases = {}
        for row in cur.fetchall():
            aliases.setdefault(row['concept_id'], []).append({'alias': row['alias']})

        # Récupération des noms étrangers
        cur.execute("""
                    SELECT "Nom_francais", "Nom_étranger", langue
                    FROM foreign_name
                    """)
        noms_etrangers = {}
        for row in cur.fetchall():
            noms_etrangers.setdefault(row['Nom francais'], []).append({
                'nom_etranger': row['Nom étranger'],
                'langue': row['langue']
            })

        # Récupération des relations
        cur.execute("""
                    SELECT *
                    FROM relations
                    """)
        relations = {}
        for row in cur.fetchall():
            relations.setdefault(row['concept_source'], []).append(dict(row))

        # Récupérer les mathématiciens et catégories
        cur.execute("SELECT id, nom FROM mathematiciens")
        mathematiciens = {row['id']: row['nom'] for row in cur.fetchall()}

        cur.execute("SELECT id, nom FROM categories")
        categories = {row['id']: row['nom'] for row in cur.fetchall()}

        # Enrichir les concepts avec les données associées
        result_concepts = []
        for concept in concepts:
            concept_dict = dict(concept)
            concept_id = concept['id']

            concept_dict['sources'] = sources.get(concept_id, [])
            concept_dict['aliases'] = aliases.get(concept_id, [])
            concept_dict['noms_etrangers'] = noms_etrangers.get(concept['nom'], [])
            concept_dict['relations'] = relations.get(concept_id, [])
            concept_dict['mathematicien'] = mathematiciens.get(concept['mathematicien_id'])
            concept_dict['categorie'] = categories.get(concept['categorie_id'])

            del concept_dict['mathematicien_id']
            del concept_dict['categorie_id']

            result_concepts.append(concept_dict)

        return result_concepts




@router.get("/getAlldatabaseInfo", response_model=List[ConceptResponse])
def giveAllDatabaseInfo():
    conn = get_db_connection()
    return get_conceptsAdmin(conn)


@router.get("/concept/{concept_id}", response_model=ConceptResponse)
def getNode(concept_id: int):
    conn = get_db_connection()
    concept = get_concept_info(concept_id, conn)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept non trouvé")
    return concept


@router.get("/getEditableFieldsOptions",response_model=EditableField)
def getEditableFieldsOptions():
    return ConceptService.getEditableFieldsOptions()


@router.patch("/update/{concept_id}",response_model=Response)
async def updateConcept(concept_id: int, data: UpdateConceptDict):
    return ConceptService.updateConcept(concept_id, data)

@router.get("/getAllConceptName",response_model=List[ConceptName])
async def get_all_concept_name_R():
    return ConceptService.get_all_concepts_name()
