from fastapi import FastAPI
import psycopg2
import psycopg2.extras
from starlette.middleware.cors import CORSMiddleware

from database import get_db_connection

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Autorise uniquement React (⚠️ sécuriser en prod)
    allow_credentials=True,
    allow_methods=["*"],  # Autorise toutes les méthodes (GET, POST, etc.)
    allow_headers=["*"],  # Autorise tous les headers
)
def get_concepts():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor.execute("SELECT id, nom,type, x, y, z FROM concepts")
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