
from aiohttp import web

from .database import PostgresDB

postgres = web.AppKey("postgres", PostgresDB)

async def init_database(app: web.Application):
    app[postgres] = await PostgresDB()
    yield
    await app[postgres].close()
