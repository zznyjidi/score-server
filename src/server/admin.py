import os

from .database import PostgresDB


async def prepare():
    global db
    db = await PostgresDB(
        host=os.getenv("POSTGRES_HOST", "127.0.0.1"), 
        port=os.getenv("POSTGRES_PORT", 5432), 
        user=os.getenv("POSTGRES_USER", "score-server"),
        password=os.getenv("POSTGRES_PASS", "password"), 
        database=os.getenv("POSTGRES_DB", "scores")
    )
