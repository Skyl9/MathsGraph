from contextlib import asynccontextmanager

from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app import settings
from app.api.routes import concept_routes, auth_routes, mathematicien_routes, categorie_routes, type_routes, \
    source_routes, relation_routes, alias_routes, graph_routes, user_routes, tags_routes, comments_routes, admin_routes, \
    statistics_routes
from app.core.logging_config import setup_logging
from app.core.exceptions import BadRequestException, NotFoundException, AuthenticationException, ForbiddenException, \
    InternalServerError, ConflictException


setup_logging()

def error_response(status_code: int, error: str):
    return {"success": False, "error": error, "data": None}

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.database import init_pool, close_pool
    await init_pool(settings.DATABASE_URL)

    try:
        yield
    finally:
        # 🧼 Fermeture propre au shutdown
        await close_pool()
app = FastAPI(
    title="Math Concepts API",
    description="API pour gérer les concepts mathématiques",
    version="1.0.0",
    docs_url="/docs",  # URL pour Swagger UI
    redoc_url="/redoc"  # URL pour ReDoc
    ,lifespan=lifespan,
    redirect_slashes=False

)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.exception_handler(BadRequestException)
async def concept_exception_handler(request: Request, exc: BadRequestException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )

@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )
@app.exception_handler(AuthenticationException)
async def not_found_exception_handler(request: Request, exc: AuthenticationException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )
@app.exception_handler(ForbiddenException)
async def not_found_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )
@app.exception_handler(InternalServerError)
async def not_found_exception_handler(request: Request, exc: InternalServerError):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )
@app.exception_handler(ConflictException)
async def not_found_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(exc.status_code, exc.detail)
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # ici on peut logger exc
    return JSONResponse(
        status_code=500,
        content=error_response(500, "Une erreur inattendue est survenue")
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
app.include_router(statistics_routes.router)
app.include_router(graph_routes.router)
app.include_router(user_routes.router)

app.include_router(tags_routes.router)

app.include_router(comments_routes.router)
app.include_router(admin_routes.router)