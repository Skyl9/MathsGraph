from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# On s'assure que l'URL utilise bien le driver asynchrone psycopg
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+psycopg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

SQLALCHEMY_DATABASE_URL = db_url

# 1. Création du moteur asynchrone (le cœur de SQLAlchemy)
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,  # Mets à True si tu veux voir le SQL généré dans la console
    pool_size=5,
    max_overflow=10,
    connect_args={"connect_timeout": 5},  # Timeout de 5 secondes pour éviter le freeze !
)

# 2. Création de l'usine à sessions
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# 3. La dépendance FastAPI pour injecter la session dans les routes
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# Note : Avec SQLAlchemy, pas besoin d'un init_pool() complexe dans le lifespan de main.py,
# le moteur gère ses connexions tout seul dès qu'on l'utilise !
