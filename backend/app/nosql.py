"""Redis (NoSQL) access layer: live vehicle telemetry, geospatial index, dashboard cache."""
import json
import redis
from app.config import settings

client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=1, socket_timeout=1)

TELEMETRY_TTL_SECONDS = 900
GEO_KEY = "fleet:positions"


def telemetry_key(vehicle_id: int) -> str:
    return f"telemetry:vehicle:{vehicle_id}"


def cache_get(key: str):
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except redis.RedisError:
        return None


def cache_set(key: str, value, ttl: int = 60) -> None:
    try:
        client.set(key, json.dumps(value, default=str), ex=ttl)
    except redis.RedisError:
        pass
