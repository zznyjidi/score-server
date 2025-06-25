
from aiohttp import web
import redis.asyncio as aioredis

from .database import PostgresDB

postgres = web.AppKey("postgres", PostgresDB)
redis = web.AppKey("redis", aioredis.Redis)

async def init_database(app: web.Application):
    app[postgres] = await PostgresDB()
    yield
    await app[postgres].close()

async def init_cache(app: web.Application):
    app[redis] = await aioredis.Redis()
    yield
    await app[redis].aclose()
