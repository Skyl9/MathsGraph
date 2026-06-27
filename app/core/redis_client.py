import redis.asyncio as redis
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)


async def invalidate_graph_cache():
    """Invalidate global graph cache and all search caches when an entity is modified."""
    try:
        await redis_db.delete("mathgraph:data")
        # Redis ne permet pas de delete en pattern via DELETE, on utilise scan_iter
        async for key in redis_db.scan_iter("mathgraph:search:*"):
            await redis_db.delete(key)
        logger.debug("Caches invalidés avec succès.")
    except Exception as e:
        logger.warning(f"Erreur lors de l'invalidation du cache: {e}")
