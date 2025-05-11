from fastapi import APIRouter
from .concept_routes import router as concept_router
from .auth_routes import router as auth_router
from .mathematicien_routes import router as mathematicien_router
from .categorie_routes import router as categorie_router
from .type_routes import router as type_router
from .source_routes import router as source_router
from .relation_routes import router as relation_router
from .alias_routes import router as alias_router
from .graph_routes import router as graph_router

api_router = APIRouter()

api_router.include_router(
    graph_router,
    prefix="/graph",
    tags=["graph"]
)
api_router.include_router(
    alias_router,
    prefix="/alias",
    tags=["alias"]
)
api_router.include_router(
    relation_router,
    prefix="/relation",
    tags=["relation"]
)
api_router.include_router(
    source_router,
    prefix="/source",
    tags=["source"]
)
api_router.include_router(
    concept_router,
    prefix="/concepts",
    tags=["concepts"]
)

api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["authentication"]
)

api_router.include_router(
    mathematicien_router,
    prefix="/mathematicien",
    tags=["mathematicien"]
)

api_router.include_router(
    categorie_router,
    prefix="/category",
    tags=["category"]
)
api_router.include_router(
    type_router,
    prefix="/type",
    tags=["type"]
)