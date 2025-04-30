from fastapi import FastAPI, HTTPException
import psycopg2.extras
from starlette.middleware.cors import CORSMiddleware

from database import get_db_connection

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Autorise uniquement React (⚠️ sécuriser en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)

def get_mathematiciens(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM mathematiciens")
        return cur.fetchall()


def get_categories(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        cur.execute("SELECT * FROM categories")
        return cur.fetchall()

def get_concept_info(concept_id, connection):
    with connection.cursor() as cursor:
        # Récupérer les informations de base sur le concept
        cursor.execute("""
            SELECT c.id, c.nom, t.type, c.enonce, c.demonstration, c.verification, c.date_modification,
                   m.id, m.nom, cat.id, cat.nom
            FROM concepts c
            LEFT JOIN mathematiciens m ON c.mathematicien_id = m.id
            LEFT JOIN categories cat ON c.categorie_id = cat.id
            LEFT JOIN type t ON c.type_id = t.id
            WHERE c.id = %s ORDER BY c.id ASC
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
            "date_ajout": result[6],
            "mathematicien":  {"id" : result[7],"mathematicien" :result[8]}
            if result[7] else None,
            "categorie": {"id":result[9], "category":result[10]}
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
        SELECT
        r.id,
        r.concept_source,
        c_source.nom AS nom_source,
        r.concept_cible,
        c_cible.nom AS nom_cible,
        r.type_relation,
        r.description,
        r.date_relation
        FROM relations r
        JOIN concepts c_source ON r.concept_source = c_source.id
        JOIN concepts c_cible ON r.concept_cible = c_cible.id
        WHERE concept_source = %s OR concept_cible = %s
        """, (concept_id, concept_id))
        concept["relations"] = [
            {
                "id": row[0],
                "concept_source": {"id":row[1],"nom":row[2]},
                "concept_cible": {"id":row[3],"nom":row[4]},
                "type_relation": row[5],
                "description":row[6],
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


def get_conceptsAdmin(conn):
    with conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
        # Récupérer les concepts
        cur.execute("SELECT * FROM concepts ORDER BY id ")
        concepts = cur.fetchall()

        # Récupération des sources liées aux concepts
        cur.execute("""
        SELECT cs.concept_id, s.* FROM concepts_sources cs
        JOIN sources s ON cs.source_id = s.id
        """)
        sources = {}
        for row in cur.fetchall():
            sources.setdefault(row['concept_id'], []).append(dict(row))

        # Récupération des alias
        cur.execute("""
        SELECT concept_id, alias FROM aliases
        """)
        aliases = {}
        for row in cur.fetchall():
            aliases.setdefault(row['concept_id'], []).append({'alias': row['alias']})

        # Récupération des noms étrangers
        cur.execute("""
        SELECT "Nom_francais", "Nom_étranger", langue FROM foreign_name
        """)
        noms_etrangers = {}
        for row in cur.fetchall():
            noms_etrangers.setdefault(row['Nom francais'], []).append({
                'nom_etranger': row['Nom étranger'],
                'langue': row['langue']
            })

        # Récupération des relations
        cur.execute("""
        SELECT * FROM relations
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



def get_concepts():
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


import psycopg2



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}





@app.get("/concepts")
def read_concepts():
    data = get_concepts()

    a = {'nodes':data,"edges":[]}
    return a

@app.get("/getAlldatabaseInfo")
def giveAllDatabaseInfo():
    conn = get_db_connection()
    return get_conceptsAdmin(conn)


@app.get("/getNode/{id}")
def getNode(id: int):
    conn = get_db_connection()
    a = get_concept_info(id, conn)
    return a

@app.patch("/updateOneCategory/{id}")
async def updateOneCategory(id: int,data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Vérifier si l'ID existe
    cursor.execute("SELECT id FROM concepts WHERE id = %s;", (id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="ID not found")

    if data["field"] in ["nom","enonce","demonstration","verification","date_ajout"]:
        set_clause = data["field"] + " = %s"  # Ex: "x = %s, y = %s"
        sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
        cursor.execute(sql, (data["value"], id))

    elif data["field"] == "type":
        cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;", (data["value"], id))

    elif data["field"] == "categorie":
        sql = f"UPDATE concepts SET categorie_id = (SELECT id FROM categories WHERE nom = %s ) WHERE id = %s;"
        cursor.execute(sql, (data["value"], id))


    elif data["field"] == "mathematicien":
        sql = f"UPDATE concepts SET mathematicien_id = (SELECT id FROM mathematiciens WHERE nom = %s ) WHERE id = %s;"
        cursor.execute(sql, (data["value"], id))


    elif data["field"] == "relations":
        cursor.execute("DELETE FROM relations WHERE concept_source = %s OR concept_cible = %s;", (id, id))
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
        cursor.execute("DELETE FROM aliases WHERE concept_id = %s;", (id,))
        for alias in data["value"]:
            cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s);", (id, alias))
    conn.commit()

    cursor.close()
    conn.close()

@app.get("/getEditableFieldsOptions/{id}")
def getEditableFieldsOptions(id: int):
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

@app.patch("/updateNodes/{id}")
async def updateNodes(id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    # Vérifier si l'ID existe
    cursor.execute("SELECT id FROM concepts WHERE id = %s;", (id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="ID not found")

    # Construction dynamique de la requête SQL
    keys = data.keys()
    for key in keys:
        if key == "type":
            cursor.execute("UPDATE concepts SET type_id = (SELECT id FROM type WHERE type = %s ) WHERE id = %s;", (data[key], id))
        else:
            set_clause =  key + " = %s"  # Ex: "x = %s, y = %s"
            sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
            cursor.execute(sql, (data[key],id))

    # Exécution de la requête

    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Mise à jour réussie", "updated_fields": data}

@app.get("/type")
async def get_type():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nom FROM categories")
    listToReturn = cursor.fetchall()
    conn.close()
    return listToReturn

@app.get("/getAllNodesNames")
async def get_name():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT nom FROM concepts Order by nom")
    listToReturn = cursor.fetchall()
    conn.close()
    return listToReturn



@app.post("/createCategory")
async def add_categories(data:dict):
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

@app.post("/createType")
async def add_categories(data:dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    cursor.execute("SELECT id FROM type WHERE type = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Type already exists")
    cursor.execute("INSERT INTO type (type) VALUES  (%s);", (data["value"],))
    conn.commit()
    cursor.close()
    conn.close()

@app.post("/createMathematicien")
async def add_categories(data:dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    cursor.execute("SELECT id FROM mathematiciens WHERE nom = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Type already exists")
    cursor.execute("INSERT INTO mathematiciens (nom) VALUES  (%s);", (data["value"],))
    conn.commit()
    cursor.close()
    conn.close()

@app.post("/createAlias")
async def add_alias(data:dict):
    conn = get_db_connection()
    cursor = conn.cursor()
    print(data)
    cursor.execute("SELECT id FROM aliases WHERE alias = %s;", (data["value"],))
    if cursor.fetchone() is not None:
        raise HTTPException(status_code=409, detail="Alias already exists")
    cursor.execute("INSERT INTO aliases (concept_id, alias) VALUES  (%s,%s);", (data["id"],data["value"]))
    conn.commit()
    cursor.close()
    conn.close()

@app.post("/createRelation")
async def add_relation(data:dict):
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

@app.post("/createSource")
async def add_source(data:dict):
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
