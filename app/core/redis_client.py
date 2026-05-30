import redis.asyncio as redis
from app.core.config import settings

redis_db = redis.from_url(settings.REDIS_URL, decode_responses=True)