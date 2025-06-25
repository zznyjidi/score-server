
import argparse
import os
from aiohttp import web
import redis.asyncio as aioredis

from .database import PostgresDB

config_key = web.AppKey("config", dict[str, str | None])
postgres_key = web.AppKey("postgres", PostgresDB)
redis_key = web.AppKey("redis", aioredis.Redis)

def parse_config(argv: list[str]) -> dict[str, str | None]:
    parser = argparse.ArgumentParser(
        prog='Score API Server', 
        description="Server for Score Storage and Leaderboard. ", 
        epilog=r'Github: https://github.com/zznyjidi/score-server'
    )
    parser.add_argument('--postgres', help='Connection URL for PostgreSQL', default=None)
    parser.add_argument('--redis', help='Connection URL for Redis', default=None)
    arg_config, _ = parser.parse_known_args(argv)

    config: dict[str, str | None] = {
        'postgres': arg_config.postgres, 
        'redis': arg_config.redis
    }

    if config['redis'] is None:
        config['redis'] = os.getenv('REDIS_URL')

    return config

async def init_database(app: web.Application):
    app[postgres_key] = await PostgresDB(dsn=app[config_key].get('postgres'))
    yield
    await app[postgres_key].close()

async def init_cache(app: web.Application):
    app[redis_key] = await aioredis.from_url(app[config_key].get('redis'))
    yield
    await app[redis_key].aclose()
