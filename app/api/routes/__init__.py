from fastapi import APIRouter
from .concept_routes import router as concept_router
from .auth_routes import router as auth_router
from .mathematicien_routes import router as mathematicien_router
from .categorie_routes import router as categorie_router

api_router = APIRouter()

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
    prefix="/mathematiciens",
    tags=["mathematiciens"]
)

api_router.include_router(
    categorie_router,
    prefix="/categories",
    tags=["categories"]
)