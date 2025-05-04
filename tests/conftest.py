import psycopg2
import pytest
from fastapi.testclient import TestClient
from psycopg2.extras import DictCursor

from app.core.security import get_password_hash
from app.main import app
from tests.constants import TEST_PASSWORD, TEST_USER_EMAIL, TEST_USER_NAME

TEST_DB_CONFIG = {
    "dbname": "test_fastapi_db",
    "user": "postgres",
    "password": "",  # Mettez ici vos informations de connexion
    "host": "localhost",
    "port": "5432"
}


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(scope="function")
def setup_test_user(setup_test_db: DictCursor):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    password_hash = get_password_hash(TEST_PASSWORD)
    try:
        cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                    (TEST_USER_NAME, TEST_USER_EMAIL, password_hash,))
        conn.commit()
        yield cur
    finally:
        cur.close()
        conn.close()


@pytest.fixture(scope="function")  # Par test, base transactionnelle.
def setup_test_db():
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    conn.autocommit = False  # Activation des transactions
    cur = conn.cursor(cursor_factory=DictCursor)
    print("Connexion à la base de données")
    try:
        # Nettoyer les tables avant chaque test
        # Désactiver temporairement les clés étrangères
        cur.execute("SET session_replication_role = 'replica';")

        # Récupérer toutes les tables depuis `information_schema`
        cur.execute("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public';
                    """)
        tables = cur.fetchall()

        # Tronquer toutes les tables
        for table in tables:
            cur.execute(f"TRUNCATE TABLE {table[0]} CASCADE;")

        # Réactiver les contraintes (fk)
        cur.execute("SET session_replication_role = 'origin';")

        # Commit
        conn.commit()
        print("Toutes les données de la base de données ont été supprimées avec succès.")

        yield cur
        print("Déconnexion à la base de données")
        conn.rollback()  # Annuler les modifications après chaque test

    except Exception as e:
        # Rollback en cas d'erreur
        if conn:
            conn.rollback()
        print("Erreur lors du nettoyage de la base de données :", e)

    finally:

        cur.close()
        conn.close()

@pytest.fixture(scope="function")
def setup_test_concept(setup_test_db: DictCursor,setup_test_type):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute("SELECT id FROM type WHERE type = %s", ("Type 1",))
        idType = cur.fetchone()["id"]
        cur.execute("INSERT INTO concepts (nom,enonce,demonstration,type,type_id) VALUES (%s,%s,%s,%s,%s)", (
            "Concept 1",
            "Enonce 1",
            "Demonstration 1",
            "axiome",
            idType
        ))
        cur.execute("SELECT id FROM concepts WHERE nom = %s", ("Concept 1",))
        id = cur.fetchone()["id"]
        conn.commit()
        yield id
    finally:
        cur.close()
        conn.close()

@pytest.fixture(scope="function")
def setup_test_mathematicien(setup_test_db: DictCursor):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute("INSERT INTO mathematiciens (nom) VALUES (%s)", (
            "Mathematicien 1"
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()

@pytest.fixture(scope="function")
def setup_test_categorie(setup_test_db: DictCursor):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute("INSERT INTO categories (nom) VALUES (%s)", (
            "Categorie 1"
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()
@pytest.fixture(scope="function")
def setup_test_type(setup_test_db: DictCursor):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute("INSERT INTO type (type) VALUES (%s)", ("Type 1",))
        conn.commit()
    finally:
        cur.close()
        conn.close()

@pytest.fixture(scope="function")
def setup_test_source(setup_test_db: DictCursor):
    conn = psycopg2.connect(
        **TEST_DB_CONFIG
    )
    cur = conn.cursor(cursor_factory=DictCursor)
    try:
        cur.execute("INSERT INTO sources (titre,auteur,annee,url,type) VALUES (%s,%s,%s,%s,%s)", (
            "Source 1",
            "Auteur 1",
        ))
        conn.commit()
    finally:
        cur.close()
        conn.close()