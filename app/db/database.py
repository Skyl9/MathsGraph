
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL
# Initialise un pool de connexions asynchrone
pool: AsyncConnectionPool = None  # Declare the pool but don't initialize it yet


# Fonction pour initialiser le pool
async def init_pool(connection_url=None):
    global pool
    if pool is None:
        pool = AsyncConnectionPool(connection_url or DATABASE_URL, open=False)
        await pool.open()
    return pool


# Fonction pour fermer le pool
async def close_pool():
    global pool
    if pool:
        await pool.close()
        pool = None


async def get_db():
    global pool
    if pool is None:
        raise ValueError(
            "Le pool de connexion n'est pas initialisé. Appelez init_pool() au démarrage de l'application.")

    async with pool.connection() as conn:
        yield conn
