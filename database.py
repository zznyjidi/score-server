import asyncpg
from argon2 import PasswordHasher

class PostgresDB:

    hasher = PasswordHasher()

    async def __init__(self, db_url: str):
        self.db: asyncpg.Connection = await asyncpg.connect(db_url)

    async def initTables(self):
        # Create user_status type
        await self.db.execute('''
            CREATE TYPE user_status AS ENUM ('active', 'unverified', 'banned', 'disabled')
        ''')

        # Create users table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid SERIAL PRIMARY KEY, 
                username text,
                display_name text,
                password_hash text, 
                status user_status
            )
        ''')

        # Create games table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS games (
                uid SERIAL PRIMARY KEY, 
                name text,
                display_name text
            )
        ''')

    async def createUser(self, username: str, display_name: str, *, password: str = None, status: str = 'unverified'):
        if not password:
            password_hash = 'null'
        else:
            password_hash = self.hasher.hash(password, salt=username)
        
        await self.db.execute('''
            INSERT INTO users(username, display_name, password_hash, status) VALUES ($1, $2, $3, $4)
        ''', username, display_name, password_hash, status)

    async def createGame(self, name: str, display_name: str):
        await self.db.execute('''
            INSERT INTO games(name, display_name) VALUES ($1, $2)
        ''', name, display_name)
