from fastapi import FastAPI, HTTPException
import psycopg2
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
def get_concepts():
    """Récupère les informations des concepts et leurs positions."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Récupérer les informations de base des concepts
    cur.execute("SELECT id, nom, type FROM concepts;")
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM concepts ORDER BY id")
    allInfo = [dict(row) for row in cursor.fetchall()]
    return allInfo


@app.get("/getNode/{id}")
def getNode(id: int):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT * FROM concepts WHERE id = %s", (id,))
    return dict(cursor.fetchone())


@app.patch("/updateNodes/{id}")
async def updateNodes(id: int, data: dict):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Vérifier si l'ID existe
    cursor.execute("SELECT id FROM concepts WHERE id = %s;", (id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="ID not found")

    # Construction dynamique de la requête SQL
    keys = data.keys()
    for key in keys:
        set_clause =  key + " = %s"  # Ex: "x = %s, y = %s"
        sql = f"UPDATE concepts SET {set_clause} WHERE id = %s;"
        cursor.execute(sql, (data[key],id))

    # Exécution de la requête

    conn.commit()

    cursor.close()
    conn.close()

    return {"message": "Mise à jour réussie", "updated_fields": data}

