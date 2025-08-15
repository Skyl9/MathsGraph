from contextlib import asynccontextmanager

import psycopg2
import psycopg2.extras
from psycopg_pool import AsyncConnectionPool

from app.core.config import settings


DATABASE_URL = settings.DATABASE_URL
# Initialise un pool de connexions asynchrone
pool: AsyncConnectionPool = None  # Declare the pool but don't initialize it yet

async def get_db():
    async with pool.connection() as conn:
        yield conn