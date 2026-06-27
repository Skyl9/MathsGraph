import datetime
import logging
import uuid
from logging.config import dictConfig

import pytest
import pytest_asyncio
from fastapi import Response
from fastapi.security import OAuth2PasswordRequestForm
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import get_db
from app.db.models import Base
from app.main import app
from app.services import AuthService
from app.services.comments_service import CommentsService
from tests.constants import TEST_PASSWORD, TEST_USER_NAME, TEST_USER_EMAIL, ADMIN_USER_NAME, ADMIN_EMAIL, ADMIN_PASSWORD


TEST_DB_CONFIG = {
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "database": "test_fastapi_db",  # FORCE TEST DB TO PREVENT ACCIDENTAL TRUNCATE
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
}
TEST_SQLALCHEMY_URL = (
    f"postgresql+psycopg://{TEST_DB_CONFIG['user']}:{TEST_DB_CONFIG['password']}"
    f"@{TEST_DB_CONFIG['host']}:{TEST_DB_CONFIG['port']}/{TEST_DB_CONFIG['database']}"
)
test_engine = create_async_engine(TEST_SQLALCHEMY_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_schema():
    """
    S'assure que la structure de la base de données de test est parfaitement
    identique à models.py en créant les tables manquantes à la volée.
    """
    async with test_engine.begin() as conn:
        # run_sync permet d'exécuter une méthode synchrone (create_all) dans le moteur async
        await conn.run_sync(Base.metadata.create_all)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Fournit une session SQLAlchemy asynchrone isolée par transaction (ROLLBACK)."""
    conn = await test_engine.connect()
    trans = await conn.begin()

    # join_transaction_mode="create_savepoint" permet aux tests de faire des commits
    # qui seront en fait des savepoints dans la transaction parente (qui sera annulée à la fin)
    session_maker = async_sessionmaker(
        bind=conn, class_=AsyncSession, expire_on_commit=False, join_transaction_mode="create_savepoint"
    )

    async with session_maker() as session:
        yield session

    await trans.rollback()
    await conn.close()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def setup_test_logging():
    """
    Configure le système de logging pour les tests.
    Définit le niveau du gestionnaire de console à DEBUG pour afficher tous les logs.
    """
    test_logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
                "level": "DEBUG",  # <<<<<< ICI : Défini le niveau du gestionnaire de console à DEBUG
            },
            # Si vous voulez également un fichier de log spécifique pour les tests,
            # vous pouvez le configurer ici. Sinon, vous pouvez supprimer ce gestionnaire.
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "standard",
                "level": "DEBUG",
                "filename": "test_app.log",  # Nom de fichier de log distinct pour les tests
                "maxBytes": 10_000_000,
                "backupCount": 1,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # logger racine
                "handlers": ["console", "file"],  # Attache les gestionnaires à la racine
                "level": "DEBUG",  # Le logger racine est aussi au niveau DEBUG
                "propagate": False,
            },
            "uvicorn.error": {"level": "WARNING"},
        },
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


@pytest_asyncio.fixture(scope="function")
async def setup_test_user(db_session: AsyncSession):
    password_hash = get_password_hash(TEST_PASSWORD)
    result = await db_session.execute(
        text(
            "INSERT INTO users (id, username, email, password_hash, is_active, role) VALUES (:id, :username, :email, :password_hash, :is_active, :role) RETURNING *"
        ),
        {
            "id": uuid.uuid4(),
            "username": TEST_USER_NAME,
            "email": TEST_USER_EMAIL,
            "password_hash": password_hash,
            "is_active": True,
            "role": "user",
        },
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_test_type(db_session: AsyncSession):
    result = await db_session.execute(
        text("INSERT INTO type (type) VALUES (:type_val) RETURNING *"), {"type_val": "Type 1"}
    )

    await db_session.commit()

    type_row = result.mappings().first()

    yield dict(type_row)


@pytest_asyncio.fixture(scope="function")
async def setup_test_concept(db_session: AsyncSession, setup_test_type):
    type_id = setup_test_type["id"]
    result = await db_session.execute(
        text(
            "INSERT INTO concepts (nom, enonce, demonstration, type_id) VALUES (:nom, :enonce, :demo, :type_id) RETURNING *"
        ),
        {"nom": "Concept 1", "enonce": "Enonce 1", "demo": "Demonstration 1", "type_id": type_id},
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_test_mathematicien(db_session: AsyncSession):
    result = await db_session.execute(
        text("INSERT INTO mathematiciens (nom) VALUES (:nom) RETURNING *"), {"nom": "Mathematicien 1"}
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_test_categorie(db_session: AsyncSession):
    result = await db_session.execute(
        text("INSERT INTO categories (nom) VALUES (:nom) RETURNING *"), {"nom": "Categorie 1"}
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_test_source(db_session: AsyncSession):
    result = await db_session.execute(
        text("INSERT INTO sources (titre, auteur) VALUES (:titre, :auteur) RETURNING *"),
        {"titre": "Source 1", "auteur": "Auteur 1"},
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_reset_token(db_session: AsyncSession, setup_test_user):
    user = setup_test_user
    time = datetime.datetime.now() + datetime.timedelta(days=1)
    result = await db_session.execute(
        text(
            "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (:user_id, :token, :expires_at) RETURNING *"
        ),
        {"user_id": user["id"], "token": "token", "expires_at": time},
    )
    await db_session.commit()
    yield dict(result.mappings().first())


# Fixture pour obtenir une instance du CommentsService
@pytest.fixture
def comments_service_instance(db_session: AsyncSession):
    return CommentsService(db_session)


@pytest_asyncio.fixture(scope="function")
async def setup_test_comment(db_session: AsyncSession, setup_test_concept, setup_test_user):
    result = await db_session.execute(
        text(
            """
             INSERT INTO comments (concept_id, user_id, content, field, parent_id)
             VALUES (:concept_id, :user_id, :content, :field, :parent_id)
             RETURNING id, concept_id, user_id, content, created_at, updated_at, parent_id, is_deleted, field
             """
        ),
        {
            "concept_id": setup_test_concept["id"],
            "user_id": setup_test_user["id"],
            "content": "Initial test comment",
            "field": "general",
            "parent_id": None,
        },
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_test_source_full(db_session: AsyncSession):
    result = await db_session.execute(
        text(
            "INSERT INTO sources (titre, auteur, annee, url, type) VALUES (:titre, :auteur, :annee, :url, :type) RETURNING *"
        ),
        {
            "titre": "Full Test Source",
            "auteur": "Full Author",
            "annee": 2020,
            "url": "http://full.com",
            "type": "livre",
        },
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_full_test_concept(
    db_session: AsyncSession,
    setup_test_type,
    setup_test_categorie,
    setup_test_mathematicien,
    setup_test_user,
    setup_test_source_full,
):
    # Insert a base concept
    result = await db_session.execute(
        text(
            """
             INSERT INTO concepts (nom, enonce, demonstration, verification, type_id, categorie_id, mathematicien_id)
             VALUES (:nom, :enonce, :demo, :verif, :type_id, :cat_id, :math_id)
             RETURNING *
             """
        ),
        {
            "nom": "Full Test Concept",
            "enonce": "Enonce complet du concept de test.",
            "demo": "Demonstration complete du concept de test.",
            "verif": True,
            "type_id": setup_test_type["id"],
            "cat_id": setup_test_categorie["id"],
            "math_id": setup_test_mathematicien["id"],
        },
    )
    concept = dict(result.mappings().first())
    concept_id = concept["id"]

    # Add aliases
    await db_session.execute(
        text("INSERT INTO aliases (concept_id, alias) VALUES (:cid, :alias1)"),
        {"cid": concept_id, "alias1": "Full Alias A"},
    )
    await db_session.execute(
        text("INSERT INTO aliases (concept_id, alias) VALUES (:cid, :alias2)"),
        {"cid": concept_id, "alias2": "Full Alias B"},
    )

    # Link the full source
    await db_session.execute(
        text("INSERT INTO concepts_sources (concept_id, source_id) VALUES (:cid, :sid)"),
        {"cid": concept_id, "sid": setup_test_source_full["id"]},
    )

    # Add a foreign name
    await db_session.execute(
        text('INSERT INTO foreign_name (concept_id, "Nom_étranger", langue) VALUES (:cid, :nom_etranger, :langue)'),
        {"cid": concept_id, "nom_etranger": "Complete Foreign Name", "langue": "en"},
    )

    # Add a related concept for relations
    res_related = await db_session.execute(
        text(
            "INSERT INTO concepts (nom, enonce, demonstration, type_id) VALUES (:nom, :enonce, :demo, :type_id) RETURNING id"
        ),
        {
            "nom": "Related Concept for Full Test",
            "enonce": "Enonce du concept lié",
            "demo": "Demo du concept lié",
            "type_id": setup_test_type["id"],
        },
    )
    related_concept_id = res_related.mappings().first()["id"]

    # Add a relation
    await db_session.execute(
        text(
            "INSERT INTO relations (concept_source, concept_cible, type_relation, description) VALUES (:c_source, :c_cible, :type_rel, :desc)"
        ),
        {
            "c_source": concept_id,
            "c_cible": related_concept_id,
            "type_rel": "implication",
            "desc": "Description de la relation complète.",
        },
    )

    await db_session.commit()

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
        "categorie": setup_test_categorie["nom"],
    }


@pytest_asyncio.fixture(scope="function")
async def setup_graph(db_session: AsyncSession, setup_test_concept):
    node = {"id": setup_test_concept["id"], "nom": setup_test_concept["nom"], "type_id": setup_test_concept["type_id"]}
    posDict = {"x": 100, "y": 100, "z": 100}
    node["position"] = posDict

    await db_session.execute(
        text("INSERT INTO positions (concept_id, x, y, z, vue) VALUES (:cid, :x, :y, :z, :vue)"),
        {"cid": setup_test_concept["id"], "x": posDict["x"], "y": posDict["y"], "z": posDict["z"], "vue": "grille"},
    )
    await db_session.commit()
    yield node


@pytest_asyncio.fixture(scope="function")
async def setup_two_concepts(db_session: AsyncSession):
    concept1_name = "Concept Source Test"
    concept2_name = "Concept Cible Test"

    # Check if type exists
    res_type = await db_session.execute(text("SELECT id FROM type WHERE type = :type"), {"type": "Type de Test"})
    type_row = res_type.mappings().first()

    if not type_row:
        res_new_type = await db_session.execute(
            text("INSERT INTO type (type) VALUES (:type) RETURNING *"), {"type": "Type de Test"}
        )
        type_row = res_new_type.mappings().first()

    type_id = type_row["id"]

    res_c1 = await db_session.execute(
        text("INSERT INTO concepts (nom, type_id, enonce) VALUES (:nom, :type_id, :enonce) RETURNING id"),
        {"nom": concept1_name, "type_id": type_id, "enonce": "Enonce 1"},
    )
    concept1_id = res_c1.mappings().first()["id"]

    res_c2 = await db_session.execute(
        text("INSERT INTO concepts (nom, type_id, enonce) VALUES (:nom, :type_id, :enonce) RETURNING id"),
        {"nom": concept2_name, "type_id": type_id, "enonce": "Enonce 2"},
    )
    concept2_id = res_c2.mappings().first()["id"]

    await db_session.commit()

    yield {
        "concept1_id": concept1_id,
        "concept1_name": concept1_name,
        "concept2_id": concept2_id,
        "concept2_name": concept2_name,
    }


@pytest_asyncio.fixture(scope="function")
async def setup_tag(db_session: AsyncSession):
    result = await db_session.execute(text("INSERT INTO tags (name) VALUES (:name) RETURNING *"), {"name": "Tag 1"})
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_tag_concept(db_session: AsyncSession, setup_test_concept):
    res_tag = await db_session.execute(text("INSERT INTO tags (name) VALUES (:name) RETURNING *"), {"name": "Tag 1"})
    tag = res_tag.mappings().first()

    await db_session.execute(
        text("INSERT INTO concept_tags (concept_id, tag_id) VALUES (:cid, :tid)"),
        {"cid": setup_test_concept["id"], "tid": tag["id"]},
    )
    await db_session.commit()
    yield dict(tag)


@pytest_asyncio.fixture(scope="function")
async def setup_fav_user(db_session: AsyncSession, setup_test_user, setup_test_concept):
    result = await db_session.execute(
        text("INSERT INTO user_favorites (user_id, concept_id) VALUES (:uid, :cid) RETURNING *"),
        {"uid": setup_test_user["id"], "cid": setup_test_concept["id"]},
    )
    await db_session.commit()
    yield dict(result.mappings().first())


@pytest_asyncio.fixture(scope="function")
async def setup_user_token_admin(db_session: AsyncSession):
    password_hash = get_password_hash(ADMIN_PASSWORD)

    await db_session.execute(
        text(
            "INSERT INTO users (id, username, email, password_hash, is_active, role) VALUES (:id, :username, :email, :password_hash, :is_active, :role)"
        ),
        {
            "id": uuid.uuid4(),
            "username": ADMIN_USER_NAME,
            "email": ADMIN_EMAIL,
            "password_hash": password_hash,
            "is_active": True,
            "role": "admin",
        },
    )
    await db_session.commit()

    login_data = {"username": ADMIN_USER_NAME, "password": ADMIN_PASSWORD}

    dummy_response = Response()

    tokenJson = await AuthService(db_session).login_for_access_token(
        OAuth2PasswordRequestForm(username=login_data["username"], password=login_data["password"]),
        response=dummy_response,
    )
    yield tokenJson
