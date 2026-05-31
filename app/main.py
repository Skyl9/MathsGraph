import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from starlette.background import BackgroundTask, BackgroundTasks
from starlette.responses import JSONResponse, RedirectResponse
import os
import asyncio

from app.api.routes import (
    concept_routes,
    auth_routes,
    mathematicien_routes,
    categorie_routes,
    type_routes,
    source_routes,
    relation_routes,
    alias_routes,
    graph_routes,
    user_routes,
    tags_routes,
    comments_routes,
    admin_routes,
    statistics_routes,
    search_routes,
)
from app.core.config import settings
from app.core.exceptions import (
    BadRequestException,
    NotFoundException,
    AuthenticationException,
    ForbiddenException,
    InternalServerError,
    ConflictException,
)
from app.core.logging_config import setup_logging
from app.core.redis_client import redis_db
from app.core.limiter import limiter
from app.db.database import AsyncSessionLocal, engine
from app.core.tasks import clean_expired_tokens_and_sessions

logger = logging.getLogger(__name__)


setup_logging()


def error_response(status_code: int, error: str):
    return {"success": False, "error": error, "data": None}


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Démarrage de l'API MathGraph...")

    # Lancement du job de nettoyage en arrière-plan
    cleanup_task = asyncio.create_task(clean_expired_tokens_and_sessions())

    yield

    logger.info("🛑 Extinction en cours, fermeture propre des pools de connexion...")

    # Annulation propre de la tâche de fond
    cleanup_task.cancel()

    await engine.dispose()

    await redis_db.close()

    logger.info("✅ Extinction terminée en toute sécurité.")


is_dev = settings.ENVIRONMENT == "development"
app = FastAPI(
    title="Math Concepts API",
    description="API pour gérer les concepts mathématiques",
    version="1.0.0",
    docs_url="/docs" if is_dev else None,
    redoc_url="/redoc" if is_dev else None,
    openapi_url="/openapi.json" if is_dev else None,
    redirect_slashes=False,
    lifespan=lifespan,
)

# Attacher le rate limiter à l'app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


async def insert_api_log(endpoint: str, method: str, status_code: int, duration_ms: float):
    """Insère un log dans la base de données en arrière-plan."""
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(
                text(
                    "INSERT INTO api_logs (endpoint, method, status_code, duration_ms) VALUES (:ep, :meth, :status, :dur)"
                ),
                {"ep": endpoint, "meth": method, "status": status_code, "dur": duration_ms},
            )
            await session.commit()
    except Exception as e:
        logger.error(f"ERREUR ANALYTICS : {e}")


@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000

    # --- Headers de sécurité ---
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if not is_dev:
        # HSTS uniquement en production (évite de casser le localhost)
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "  # unsafe-inline requis pour React/Vite en prod
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )

    # --- Logging des appels API ---
    ignored_paths = ["/docs", "/openapi.json", "/redoc"]
    if not any(request.url.path.startswith(p) for p in ignored_paths):
        log_task = BackgroundTask(
            insert_api_log,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=process_time,
        )
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
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(AuthenticationException)
async def authentication_exception_handler(request: Request, exc: AuthenticationException):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(ForbiddenException)
async def forbidden_exception_handler(request: Request, exc: ForbiddenException):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(InternalServerError)
async def internal_server_error_handler(request: Request, exc: InternalServerError):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(ConflictException)
async def conflict_exception_handler(request: Request, exc: ConflictException):
    return JSONResponse(status_code=exc.status_code, content=error_response(exc.status_code, exc.detail))


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Erreur non gérée sur la route {request.method} {request.url.path}")

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Une erreur inattendue est survenue côté serveur.",
            "data": None,
            "meta": None,
        },
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


@app.get("/")
async def redirect_to_new_domain():
    """
    Route catch-all pour rediriger le trafic de l'ancien domaine (Railway)
    vers le nouveau domaine (Scaleway).
    """
    target_url = os.getenv("NEW_FRONTEND_URL", "https://mathsgraph.com")
    return RedirectResponse(url=target_url, status_code=301)
