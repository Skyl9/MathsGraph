import psycopg2
import psycopg2.extras
from app.core.config import settings

def get_db_connection():
    return psycopg2.connect(settings.DATABASE_URL)