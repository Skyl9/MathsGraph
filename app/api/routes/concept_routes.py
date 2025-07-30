import psycopg2
from fastapi import APIRouter, HTTPException

from app.db.database import get_db_connection
from app.schemas import CategorieBase
from app.schemas.EditableClass import EditableField
from app.schemas.GraphData import Nodes, GraphData
from app.schemas.concept import ConceptResponse, ConceptName, RollbackConcept
from app.schemas.history import History
from app.schemas.mathematicien import MathematicienResponse
from app.schemas.pathcClass import UpdateConceptDict
from app.schemas.response import Response
from typing import List

from app.services.concept_service import ConceptService

#TODO Modifier updateOneCategory pour prendre en compte si utilisateur + historique

router = APIRouter(prefix="", tags=["concepts"])


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
def getConcept(concept_id: int):
    return ConceptService.get_concept_info(concept_id)

@router.patch("/concept/rollback/{concept_id}")
async def rollbackConcept(concept_id: int,data: RollbackConcept):
    return ConceptService.rollback_history(concept_id,data)

@router.get("/getEditableFieldsOptions", response_model=EditableField)
def getEditableFieldsOptions():
    return ConceptService.getEditableFieldsOptions()


@router.get("/concept/history/{concept_id}", response_model=List[History])
def getHistory(concept_id: int):
    return ConceptService.get_concept_versions(concept_id)


@router.patch("/update/{concept_id}", response_model=Response)
async def updateConcept(concept_id: int, data: UpdateConceptDict):
    return ConceptService.updateConcept(concept_id, data)


@router.get("/getAllConceptName", response_model=List[ConceptName])
async def get_all_concept_name_R():
    return ConceptService.get_all_concepts_name()
