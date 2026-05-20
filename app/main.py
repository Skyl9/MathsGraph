import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.responses import JSONResponse

from app import settings
from app.api.routes import concept_routes, auth_routes, mathematicien_routes, categorie_routes, type_routes, \
    source_routes, relation_routes, alias_routes, graph_routes, user_routes, tags_routes, comments_routes, admin_routes, \
    statistics_routes, search_routes
from app.core.exceptions import BadRequestException, NotFoundException, AuthenticationException, ForbiddenException, \
    InternalServerError, ConflictException
from app.core.logging_config import setup_logging
from app.core.redis_client import redis_db
from app.db.database import AsyncSessionLocal, engine

setup_logging()

logger = logging.getLogger(__name__)


def error_response(status_code: int, error: str):
    return {"success": False, "error": error, "data": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage de l'API MathGraph...")

    yield

    logger.info("🛑 Extinction en cours, fermeture propre des pools de connexion...")

    await engine.dispose()

    await redis_db.close()

    logger.info("✅ Extinction terminée en toute sécurité.")


is_dev = settings.ENVIRONMENT == "development"
app = FastAPI(
    title="Math Concepts API",
    description="API pour gérer les concepts mathématiques",
    version="1.0.0",
    docs_url="/docs" if is_dev else None,  # URL pour Swagger UI
    redoc_url="/redoc" if is_dev else None,  # URL pour ReDoc
    openapi_url="/openapi.json" if is_dev else None,  # Cache aussi le fichier JSON brut
    redirect_slashes=False,
    lifespan=lifespan

)


async def insert_api_log(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Insère un log dans la base de données en arrière-plan."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text(
                "INSERT INTO api_logs (endpoint, method, status_code, duration_ms) VALUES (:ep, :meth, :status, :dur)"),
                {"ep": endpoint, "meth": method, "status": status_code, "dur": duration_ms}
            )
            await session.commit()
    except Exception as e:
        logger.error(f"ERREUR ANALYTICS : {e}")


@app.middleware("http")
async def log_api_calls(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    ignored_paths = ["/docs", "/openapi.json", "/redoc"]

    if not any(request.url.path.startswith(p) for p in ignored_paths):
        # 1. On prépare la tâche d'arrière-plan
        log_task = BackgroundTask(
            insert_api_log,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=process_time
        )

        # On vérifie si une autre route a déjà créé une tâche de fond pour ne pas l'écraser
        if response.background is None:
            response.background = log_task
        else:
            new_tasks = BackgroundTasks()
            new_tasks.add_task(response.background)
            new_tasks.add_task(log_task)
            response.background = new_tasks

    return response


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
    logger.exception(f"Erreur non gérée sur la route {request.method} {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Une erreur inattendue est survenue côté serveur.", "data": None,
                 "meta": None}
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

app.include_router(search_routes.router)
