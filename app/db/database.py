from contextlib import asynccontextmanager

import psycopg2
import psycopg2.extras
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL
# Initialise un pool de connexions asynchrone
pool = AsyncConnectionPool(DATABASE_URL, open=False)

async def get_db():
    async with pool.connection() as conn:
        yield conn


def get_db_connection():
    return psycopg2.connect(settings.DATABASE_URL)