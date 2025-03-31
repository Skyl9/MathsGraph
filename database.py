import os
import psycopg2
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

def get_db_connection():
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        return conn
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion à PostgreSQL : {e}")
        return None  # Permet d'éviter les plantages si la connexion échoue
