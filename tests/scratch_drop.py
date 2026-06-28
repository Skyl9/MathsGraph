import asyncio
import os
import sys

from app.db.models import Base
from tests.conftest import test_engine

# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def drop_all():
    async with test_engine.begin() as conn:
        print("Dropping all tables in test database...")
        await conn.run_sync(Base.metadata.drop_all)
        print("Tables dropped.")


if __name__ == "__main__":
    asyncio.run(drop_all())
