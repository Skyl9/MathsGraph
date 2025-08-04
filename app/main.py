from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import concept_routes, auth_routes, mathematicien_routes, categorie_routes, type_routes, \
    source_routes, relation_routes, alias_routes, graph_routes, user_routes, tags_routes, comments_routes, admin_routes
from app.db.database import pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ⚡ Ouverture du pool au démarrage
    await pool.open()
    try:
        yield
    finally:
        # 🧼 Fermeture propre au shutdown
        await pool.close()
app = FastAPI(
    title="Math Concepts API",
    description="API pour gérer les concepts mathématiques",
    version="1.0.0",
    docs_url="/docs",  # URL pour Swagger UI
    redoc_url="/redoc"  # URL pour ReDoc
    ,lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(concept_routes.router)
app.include_router(auth_routes.router)
app.include_router(mathematicien_routes.router)
app.include_router(categorie_routes.router)
app.include_router(type_routes.router)
app.include_router(alias_routes.router)
app.include_router(relation_routes.router)

app.include_router(source_routes.router)

app.include_router(graph_routes.router)
app.include_router(user_routes.router)

app.include_router(tags_routes.router)

app.include_router(comments_routes.router)
app.include_router(admin_routes.router)