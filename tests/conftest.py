import asyncio
import logging
from datetime import datetime, timedelta
from logging.config import dictConfig

import psycopg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from psycopg_pool import AsyncConnectionPool

from app.core.security import get_password_hash
from app.db import database
from app.db.database import get_db
from app.main import app
from tests.constants import TEST_PASSWORD, TEST_USER_EMAIL, TEST_USER_NAME

TEST_DB_CONFIG = {
    "user": "postgres",
    "password": "",
    "database": "test_fastapi_db",
    "host": "localhost",
    "port": "5432",
}
url = (
    f"postgresql://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}"
    f"@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}"
)

@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """
    Configure le système de logging pour les tests.
    Définit le niveau du gestionnaire de console à DEBUG pour afficher tous les logs.
    """
    test_logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG"  # <<<<<< ICI : Défini le niveau du gestionnaire de console à DEBUG
            },
            # Si vous voulez également un fichier de log spécifique pour les tests,
            # vous pouvez le configurer ici. Sinon, vous pouvez supprimer ce gestionnaire.
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": "test_app.log", # Nom de fichier de log distinct pour les tests
                "maxBytes": 10_000_000,
                "backupCount": 1,
                "encoding": "utf8"
            }
        },
        "loggers": {
            "": {                       # logger racine
                "handlers": ["console", "file"], # Attache les gestionnaires à la racine
                "level": "DEBUG",      # Le logger racine est aussi au niveau DEBUG
                "propagate": False
            },
            "uvicorn.error": {
                "level": "WARNING"
            }
        }
    }

    # Applique la configuration de logging spécifique aux tests
    dictConfig(test_logging_config)

    # Optionnel : log de vérification que le setup est bien appliqué
    logging.info("Configuration de logging appliquée pour la session de tests (DEBUG console).")

    # `yield` permet aux tests de s'exécuter
    yield

    # Optionnel : Réinitialiser la configuration de logging après les tests
    # Cela peut être utile pour éviter des interférences si d'autres parties de votre
    # environnement de test ou des exécutions ultérieures nécessitent une configuration différente.
    for handler in logging.getLogger().handlers[:]:
        logging.getLogger().removeHandler(handler)
        handler.close()
    logging.info("Configuration de logging réinitialisée après la session de tests.")


# Event loop session-scoped pour compatibilité fixtures session async
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_db():
    pool = AsyncConnectionPool(url)
    await pool.open()
    yield pool
    await pool.close()

@pytest_asyncio.fixture(scope="function")
async def transaction(async_db: AsyncConnectionPool):
    print("\n--- Début de la transaction (Rollback forcé) ---")
    async with async_db.connection() as conn:
        print(f"Connexion obtenue : {conn.info.backend_pid}")
        await conn.execute("BEGIN")
        print("\n--- Transaction de test DÉMARRÉE (BEGIN) ---")

        try:
            yield conn
        finally:
            await conn.execute("ROLLBACK")
            print("--- Transaction de test ANNULÉE (ROLLBACK) ---")


@pytest_asyncio.fixture(scope="function")
async def async_client(transaction: psycopg.AsyncConnection):
    # La surcharge doit être un générateur asynchrone qui yield la connexion transactionnelle.

    async def override_get_db():
        yield transaction

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def setup_test_user(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        password_hash = get_password_hash(TEST_PASSWORD)
        await cur.execute(
            "INSERT INTO users (username, email, password_hash, is_active, role) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            (TEST_USER_NAME, TEST_USER_EMAIL, password_hash, True, 'user')
        )
        user = await cur.fetchone()
    yield user

@pytest_asyncio.fixture(scope="function")
async def setup_test_type(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO type (type) VALUES (%s) RETURNING *", ("Type 1",))
        type_row = await cur.fetchone()
    yield type_row

@pytest_asyncio.fixture(scope="function")
async def setup_test_concept(transaction: psycopg.AsyncConnection, setup_test_type: psycopg.rows.dict_row):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        type_id = setup_test_type['id']
        await cur.execute(
            "INSERT INTO concepts (nom,enonce,demonstration,type_id) VALUES (%s,%s, %s, %s) RETURNING *",
            ("Concept 1", "Enonce 1", "Demonstration 1", type_id)
        )
        concept = await cur.fetchone()
    yield concept

@pytest_asyncio.fixture(scope="function")
async def setup_test_mathematicien(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO mathematiciens (nom) VALUES (%s) RETURNING *", ("Mathematicien 1",))
        mat = await cur.fetchone()
    yield mat

@pytest_asyncio.fixture(scope="function")
async def setup_test_categorie(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO categories (nom) VALUES (%s) RETURNING *", ("Categorie 1",))
        cat = await cur.fetchone()
    yield cat

@pytest_asyncio.fixture(scope="function")
async def setup_test_source(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(
            "INSERT INTO sources (titre,auteur) VALUES (%s, %s) RETURNING *",
            ("Source 1", "Auteur 1")
        )
        src = await cur.fetchone()
    yield src

@pytest_asyncio.fixture(scope="function")
async def setup_reset_token(transaction:psycopg.AsyncConnection,setup_test_user):
    user = setup_test_user
    time = datetime.now() + timedelta(days=1)
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(
            "INSERT INTO password_reset_tokens (user_id, token,expires_at) VALUES (%s, %s,%s) RETURNING *",
            (user["id"], "token",time)
        )
        reset_data= await cur.fetchone()
    yield reset_data