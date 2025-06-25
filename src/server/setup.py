
from aiohttp import web
import redis.asyncio as aioredis

from .database import PostgresDB

config_key = web.AppKey("config", dict[str, str | None])
postgres_key = web.AppKey("postgres", PostgresDB)
redis_key = web.AppKey("redis", aioredis.Redis)

async def init_database(app: web.Application):
    app[postgres_key] = await PostgresDB(dsn=app[config_key].get('postgres'))
    yield
    await app[postgres_key].close()

async def init_cache(app: web.Application):
    app[redis_key] = await aioredis.from_url(app[config_key].get('redis'))
    yield
    await app[redis_key].aclose()
