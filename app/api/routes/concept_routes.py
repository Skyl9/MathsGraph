from pprint import pprint

import psycopg2
from fastapi import APIRouter, HTTPException, Depends

from app.core.deps import get_current_active_user
from app.core.exceptions import ConceptException
from app.db.database import get_db_connection
from app.schemas import CategorieBase
from app.schemas.EditableClass import EditableField
from app.schemas.GraphData import Nodes, GraphData
from app.schemas.Views import Views
from app.schemas.concept import ConceptCreate, ConceptResponse
from app.schemas.mathematicien import MathematicienResponse
from app.schemas.pathcClass import UpdateCategoryDict, CreateData, CreateAlias, CreateRelation, CreateSource
from app.schemas.response import Response
from app.services.concept_service import ConceptService
from typing import List

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
            "categories": {"id": result[9], "category": result[10]}
            if result[9] else None,
        }

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


def get_concepts() -> Nodes:
    """Récupère les informations des concepts et leurs positions."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Récupérer les informations de base des concepts
    cur.execute("SELECT c.id, c.nom, t.type FROM concepts c LEFT JOIN type t on type_id = t.id ORDER BY id ;")
    concepts = cur.fetchall()

    # Récupérer les positions des concepts
    cur.execute("SELECT concept_id, vue, x, y, z FROM positions WHERE vue IN ('grille', 'arbre');")
    positions = cur.fetchall()

    # Créer un dictionnaire de positions par concept_id
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

    return result


@router.get("/concepts", response_model=GraphData)
async def read_concepts():
    data = get_concepts()

    a = {'nodes': data, "edges": []}
    return a


@router.get("/getAlldatabaseInfo", response_model=List[ConceptResponse])
def giveAllDatabaseInfo():
    conn = get_db_connection()
    return get_conceptsAdmin(conn)


@router.get("/getNode/{concept_id}", response_model=ConceptResponse)
def getNode(concept_id: int):
    conn = get_db_connection()
    concept = get_concept_info(concept_id, conn)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept non trouvé")
    return concept


@router.patch("/updateOneCategory/{concept_id}")
async def updateOneCategory(concept_id: int, data: UpdateCategoryDict):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Vérifier si l'ID existe
    cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="ID not found")

    if data["field"] in ["nom", "enonce", "demonstration", "verification", "date_ajout"]:
        set_clause = data["field"] + " = %s"  # Ex: "x = %s, y = %s"
        sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
        cursor.execute(sql, (data["value"], concept_id))

    elif data["field"] == "type":
        cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;",
                       (data["value"], concept_id))

    elif data["field"] == "categorie":
        sql = f"UPDATE concepts SET categorie_id = (SELECT id FROM categories WHERE nom = %s ) WHERE id = %s;"
        cursor.execute(sql, (data["value"], concept_id))


    elif data["field"] == "mathematicien":
        sql = f"UPDATE concepts SET mathematicien_id = (SELECT id FROM mathematiciens WHERE nom = %s ) WHERE id = %s;"
        cursor.execute(sql, (data["value"], concept_id))


    elif data["field"] == "relations":
        cursor.execute("DELETE FROM relations WHERE concept_source = %s OR concept_cible = %s;", (concept_id, concept_id))
        for relation in data["value"]:
            cursor.execute("""
                INSERT INTO relations (concept_source, concept_cible, type_relation, description)
                VALUES (%s, %s, %s, %s);
            """, (
                relation["concept_source"]["id"],
                relation["concept_cible"]["id"],
                relation["type_relation"],
                relation.get("description"),
            ))

    elif data["field"] == "sources":
        for source in data["value"]:
            cursor.execute("UPDATE sources SET titre = %s,auteur = %s,annee = %s,url = %s,type = %s  WHERE id = %s ;", (source["titre"], source["auteur"], source["annee"], source["url"], source["type"],source["id"]))

    elif data["field"] == "aliases":
        cursor.execute("DELETE FROM aliases WHERE concept_id = %s;", (concept_id,))
        for alias in data["value"]:
            cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s);", (concept_id, alias))
    conn.commit()

    cursor.close()
    conn.close()

@router.get("/concepts/{concept_id}/views",response_model=Views)
async def get_concept_views(concept_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT COUNT(*) as view_count,
                   COUNT(DISTINCT user_id) as unique_viewers
            FROM concept_views
            WHERE concept_id = %s
        """, (concept_id,))
        result = cursor.fetchone()
        return {"total_views": result[0], "unique_viewers": result[1]}
    finally:
        cursor.close()
        conn.close()

@router.get("/getEditableFieldsOptions",response_model=EditableField)
def getEditableFieldsOptions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT type FROM type")
    type_concept = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT nom FROM categories")
    category = [r[0] for r in cursor.fetchall()]
    cursor.execute("SELECT DISTINCT nom FROM mathematiciens")
    mathematiciens = [r[0] for r in cursor.fetchall()]
    data = {"mathematicien": mathematiciens,
            "categorie": category,
            "type": type_concept}
    return data



"""
@router.get("/{concept_id}", response_model=ConceptResponse)
async def get_node(concept_id: int):
    concept = ConceptService.get_concept_by_id(concept_id)
    if not concept:
        raise HTTPException(status_code=404, detail="Concept non trouvé")
    return concept

"""
@router.patch("/updateNodes/{concept_id}",response_model=Response)
async def updateNodes(concept_id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    # Vérifier si l'ID existe
    cursor.execute("SELECT id FROM concepts WHERE id = %s;", (concept_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="ID not found")

    # Construction dynamique de la requête SQL
    keys = data.keys()
    for key in keys:
        if key == "type":
            cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;", (data[key], concept_id))
        else:
            set_clause =  key + " = %s"  # Ex: "x = %s, y = %s"
            sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
            cursor.execute(sql, (data[key], concept_id))

    # Exécution de la requête

    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Mise à jour réussie", "status":404,"data": data}

@router.get("/type",response_model=List[str])
async def get_type_names():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nom FROM categories")
    listNameCategory = cursor.fetchall()
    conn.close()
    return listNameCategory

@router.get("/getAllNodesNames",response_model=List[str])
async def get_nodes_names():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nom FROM concepts Order by nom")
    conceptNameList = cursor.fetchall()
    conn.close()
    return conceptNameList



@router.post("/createCategory")
async def add_categories(data:CreateData):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    cursor.execute("SELECT id FROM categories WHERE nom = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Category already exists")
    cursor.execute("INSERT INTO categories (nom) VALUES  (%s);", (data["value"],))
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/createType")
async def add_categories(data:CreateData):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM type WHERE type = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Type already exists")
    cursor.execute("INSERT INTO type (type) VALUES  (%s);", (data["value"],))
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/createMathematicien")
async def add_categories(data:CreateData):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Type already exists")
    cursor.execute("INSERT INTO mathematiciens (nom) VALUES  (%s);", (data["value"],))
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/createAlias")
async def add_alias(data: CreateAlias):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM aliases WHERE alias = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Alias already exists")
    cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES  (%s,%s);", (data["id"],data["value"]))
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/createRelation")
async def add_relation(data:CreateRelation):
    data = data["value"]
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data["théo1"].strip(),data["théo2"])
    cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo1"],))
    theo1 = cursor.fetchone()
    cursor.execute("SELECT id FROM concepts WHERE TRIM(nom) = %s;", (data["théo2"],))
    theo2 = cursor.fetchone()
    cursor.execute("SELECT id FROM relations WHERE concept_source = %s AND concept_cible = %s;", (theo1,theo2))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Relation already exists")
    if theo1 is None or theo2 is None:
        print(theo1,theo2)
        raise HTTPException(status_code=404, detail="Concept not found")
    cursor.execute("INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES  (%s,%s,%s,%s);", (theo1[0],theo2[0], data["relation"], data["desc"]))
    conn.commit()
    cursor.close()
    conn.close()

@router.post("/createSource")
async def add_source(data:CreateSource):
    data = data["value"]
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    cursor.execute("SELECT id FROM sources WHERE titre = %s;", (data["source"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Source already exists")
    cursor.execute("INSERT INTO sources (titre,auteur,annee,url,type) VALUES  (%s,%s,%s,%s,%s) RETURNING id;", (data["source"],data["auteur"],data["annee"],data["url"],data["type"]))
    source_id = cursor.fetchone()[0]
    cursor.execute("INSERT INTO concepts_sources (concept_id, source_id) VALUES  (%s,%s);", (data["id"],source_id))
    conn.commit()
    cursor.close()
    conn.close()