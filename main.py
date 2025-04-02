from fastapi import FastAPI, HTTPException
import psycopg2
import psycopg2.extras
from starlette.middleware.cors import CORSMiddleware

from database import get_db_connection

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mathsgraphfrontend-production.up.railway.app",
                   "http://localhost:3000"],  # Autorise uniquement React (⚠️ sécuriser en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)
def get_concepts():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, nom,type, x, y, z FROM concepts ORDER BY id")
    concepts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return concepts


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}





@app.get("/concepts")
def read_concepts():
    data = get_concepts()
    L = []
    for i in data:
        dictio = {"id":i["id"],'nom':i["nom"],'typeMath':i['type'],'position':[i["x"],i["y"],i["z"]]}
        L.append(dictio)
    a = {'nodes':L,"edges":[],}
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

