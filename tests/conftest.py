import asyncio
import logging
from datetime import datetime, timedelta
from logging.config import dictConfig

import psycopg
import pytest
import pytest_asyncio
from httpx import AsyncClient
from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool

from app.core.security import get_password_hash
from app.db import database
from app.db.database import get_db
from app.main import app
from app.services.comments_service import CommentsService
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

# Fixture pour obtenir une instance du CommentsService avec une connexion transactionnelle
@pytest.fixture
def comments_service_instance(transaction: psycopg.AsyncConnection):
    return CommentsService(transaction)

# Fixture pour créer un commentaire de test (à ajouter à votre conftest.py si ce n'est pas déjà fait)
@pytest_asyncio.fixture(scope="function")
async def setup_test_comment(transaction: psycopg.AsyncConnection, setup_test_concept, setup_test_user):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO comments (concept_id, user_id, content, field, parent_id)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, concept_id, user_id, content, created_at, updated_at, parent_id, is_deleted, field
            """,
            (setup_test_concept["id"], setup_test_user["id"], "Initial test comment", "general", None)
        )
        comment = await cur.fetchone()
    yield comment

@pytest_asyncio.fixture(scope="function")
async def setup_test_source_full(transaction: psycopg.AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(
            "INSERT INTO sources (titre, auteur, annee, url, type) VALUES (%s, %s, %s, %s, %s) RETURNING *",
            ("Full Test Source", "Full Author", 2020, "http://full.com", "livre")
        )
        source = await cur.fetchone()
    yield source


@pytest_asyncio.fixture(scope="function")
async def setup_full_test_concept(
        transaction: psycopg.AsyncConnection,
        setup_test_type,
        setup_test_categorie,
        setup_test_mathematicien,
        setup_test_user,  # Pour les logs d'historique
        setup_test_source_full  # Utiliser la nouvelle fixture de source complète
):
    # Insert a base concept
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute(
            """
            INSERT INTO concepts (nom, enonce, demonstration, verification, type_id, categorie_id, mathematicien_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                "Full Test Concept",
                "Enonce complet du concept de test.",
                "Demonstration complete du concept de test.",
                True,
                setup_test_type["id"],
                setup_test_categorie["id"],
                setup_test_mathematicien["id"]
            )
        )
        concept = await cur.fetchone()
        concept_id = concept["id"]

        # Add aliases
        await cur.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s)", (concept_id, "Full Alias A"))
        await cur.execute("INSERT INTO aliases (concept_id, alias) VALUES (%s, %s)", (concept_id, "Full Alias B"))

        # Link the full source
        await cur.execute("INSERT INTO concepts_sources (concept_id, source_id) VALUES (%s, %s)",
                          (concept_id, setup_test_source_full["id"]))

        # Add a foreign name
        await cur.execute("INSERT INTO foreign_name (concept_id, \"Nom_étranger\", langue) VALUES (%s, %s, %s)",
                          (concept_id, "Complete Foreign Name", "en"))

        # Add a related concept for relations
        await cur.execute(
            "INSERT INTO concepts (nom, enonce, demonstration, type_id) VALUES (%s, %s, %s, %s) RETURNING id",
            ("Related Concept for Full Test", "Enonce du concept lié", "Demo du concept lié", setup_test_type["id"])
        )
        related_concept = await cur.fetchone()
        related_concept_id = related_concept["id"]

        # Add a relation
        await cur.execute(
            "INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES (%s, %s, %s, %s)",
            (concept_id, related_concept_id, "implication", "Description de la relation complète.")
        )

        # Add an initial history entry (for 'nom' change, simulating an update)
        # We need the ConceptService.add_concept_version for this, but for API tests,
        # we usually trigger history via a PATCH call. For this setup, we'll
        # simulate it if strictly needed for GET history tests.
        # For now, let's just make sure the fixture returns the concept and associated IDs.

    # Return the main concept and some associated IDs for testing
    yield {
        "concept": concept,
        "aliases": ["Full Alias A", "Full Alias B"],
        "source": setup_test_source_full,
        "foreign_name": {"Nom_étranger": "Complete Foreign Name", "langue": "en"},
        "related_concept_id": related_concept_id,
        "user_id": setup_test_user["id"],
        "username": setup_test_user["username"],
        "type": setup_test_type["type"],
        "mathematicien": setup_test_mathematicien["nom"],
        "categorie": setup_test_categorie["nom"]
    }
@pytest_asyncio.fixture(scope="function")
async def setup_graph(transaction,setup_test_concept):
    node = {"id": setup_test_concept["id"],"nom":setup_test_concept["nom"],"type_id":setup_test_concept["type_id"]}
    posDict = {"x": 100, "y": 100,"z": 100}
    node["position"] = posDict
    async with transaction.cursor() as cur:
        await cur.execute("INSERT INTO positions (concept_id,x,y,z,vue) VALUES (%s,%s,%s,%s,%s) RETURNING * ", (setup_test_concept["id"],posDict["x"],posDict["y"],posDict["z"],"grille"))
    yield node

@pytest_asyncio.fixture(scope="function")
async def setup_two_concepts(transaction: AsyncConnection):
    """
    Fixture pour configurer deux concepts pour les tests de relation.
    Insère deux concepts et s'assure qu'ils sont nettoyés après le test.
    """
    concept1_name = "Concept Source Test"
    concept2_name = "Concept Cible Test"
    concept1_id = None
    concept2_id = None
    type_id = None
    async with transaction.cursor() as cur:
        # Assurez-vous qu'un type existe pour les concepts
        await cur.execute("INSERT INTO type (type) VALUES (%s) RETURNING *;", ("Type de Test",))

        result = await cur.fetchone()
        if result:
            type_id = result[0]
        else:
            await cur.execute("SELECT id FROM type WHERE type = %s;", ("Type de Test",))
            type_id = (await cur.fetchone())[0]

        # Insérer le Concept Source
        await cur.execute(
            "INSERT INTO concepts (nom, type_id,enonce) VALUES (%s, %s,%s) RETURNING *;",
            (concept1_name, type_id,"Enonce 1")
        )
        concept1_id = (await cur.fetchone())[0]

        # Insérer le Concept Cible
        await cur.execute(
            "INSERT INTO concepts (nom, type_id,enonce) VALUES (%s, %s,%s) RETURNING *;",
            (concept2_name, type_id,"Enonce 2")
        )
        concept2_id = (await cur.fetchone())[0]
        # Commit pour que les concepts soient visibles pour les opérations suivantes dans la même transaction de test
    yield {
        "concept1_id": concept1_id,
        "concept1_name": concept1_name,
        "concept2_id": concept2_id,
        "concept2_name": concept2_name,
    }

@pytest_asyncio.fixture(scope="function")
async def setup_tag(transaction: AsyncConnection):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO tags (name) VALUES (%s) RETURNING *;", ("Tag 1",))
        tag = await cur.fetchone()
    yield tag

@pytest_asyncio.fixture(scope="function")
async def setup_tag_concept(transaction: AsyncConnection,setup_test_concept):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO tags (name) VALUES (%s) RETURNING *;", ("Tag 1",))
        tag = await cur.fetchone()
        await cur.execute("INSERT INTO concept_tags (concept_id, tag_id) VALUES (%s, %s) RETURNING *;", (setup_test_concept["id"],tag["id"]))
    yield tag

@pytest_asyncio.fixture(scope="function")
async def setup_fav_user(transaction: AsyncConnection,setup_test_user,setup_test_concept):
    async with transaction.cursor(row_factory=psycopg.rows.dict_row) as cur:
        await cur.execute("INSERT INTO user_favorites (user_id, concept_id) VALUES (%s, %s) RETURNING *;", (setup_test_user["id"],setup_test_concept["id"]))
        fav = await cur.fetchone()
    yield fav