import os

from database import PostgresDB

async def prepare():
    global db
    db = await PostgresDB(
        host=os.getenv("POSTGRES_HOST", "db"), 
        port=os.getenv("POSTGRES_PORT", 5432), 
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASS", None), 
        database=os.getenv("POSTGRES_DB", "scores")
    )
