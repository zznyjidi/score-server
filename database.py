from enum import StrEnum
from typing import Optional

import asyncpg
import asyncpg.prepared_stmt
from argon2 import PasswordHasher
from email_validator import EmailNotValidError, validate_email


class userStatus(StrEnum):
    Active = 'active'
    Unverified = 'unverified'
    Banned = 'banned'
    Disabled = 'disabled'

class PostgresDB:

    hasher = PasswordHasher()

    # For async init
    async def __new__(cls, *a, **kw):
        instance = super().__new__(cls)
        await instance.__init__(*a, **kw)
        return instance

    async def __init__(self, db_url: str):
        self.db: asyncpg.Connection = await asyncpg.connect(db_url)
        try:
            self.fetchUserByUid: asyncpg.prepared_stmt.PreparedStatement = await self.db.prepare('SELECT * FROM users WHERE uid = $1')
            self.fetchUserByUsername: asyncpg.prepared_stmt.PreparedStatement = await self.db.prepare('SELECT * FROM users WHERE username = $1')
            self.fetchUserByNickname: asyncpg.prepared_stmt.PreparedStatement = await self.db.prepare('SELECT * FROM users WHERE display_name = $1')
            self.fetchUserByEmail: asyncpg.prepared_stmt.PreparedStatement = await self.db.prepare('SELECT * FROM users WHERE lower(email) = LOWER($1)')
        except asyncpg.exceptions.UndefinedTableError:
            await self.initTables()

    async def initTables(self):
        """### Create Type user_status and Table users and games
        """
        # Create user_status type
        await self.db.execute('''
            CREATE TYPE user_status AS ENUM ('active', 'unverified', 'banned', 'disabled')
        ''')

        # Create users table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                uid SERIAL PRIMARY KEY, 
                username text,
                email text,
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

    async def searchUserByUid(self, uid: int) -> list[asyncpg.Record]:
        """### Get All Users with the uid

        Args:
            uid (int): uid to fetch

        Returns:
            list[asyncpg.Record]: users with the uid
        """
        return await self.fetchUserByUid.fetch(uid)

    async def searchUserByUsername(self, username: str) -> list[asyncpg.Record]:
        """### Get All Users with the username

        Args:
            username (str): username to fetch

        Returns:
            list[asyncpg.Record]: users with the username
        """
        return await self.fetchUserByUsername.fetch(username)

    async def searchUserByNickname(self, nickname: str) -> list[asyncpg.Record]:
        """### Get All Users with the nickname

        Args:
            nickname (str): nickname to fetch

        Returns:
            list[asyncpg.Record]: users with the nickname
        """
        return await self.fetchUserByNickname.fetch(nickname)
    
    async def searchUserByEmail(self, email: str) -> list[asyncpg.Record]:
        """### Get All Users with the email

        Args:
            email (str): email to fetch

        Returns:
            list[asyncpg.Record]: users with the email
        """
        return await self.fetchUserByEmail.fetch(email)

    async def createUser(self, username: str, display_name: str, email: str, *, password: str = None, status: userStatus = 'unverified') -> Optional[str]:
        """### Create User in db

        Args:
            username (str): username
            display_name (str): nickname
            email (str): email
            password (str, optional): password. Defaults to None.
            status (userStatus, optional): status of the user. Defaults to 'unverified'.

        Returns:
            Optional[str]: error message
        """
        if not username:
            return 'Username can\'t be empty! '
        if not display_name:
            return 'Nickname can\'t be empty! '
        if not email:
            return 'Email cat\'t be empty! '
        if await self.searchUserByUsername(username):
            return 'Username already exist. '
        if await self.searchUserByNickname(display_name):
            return 'Nickname already exist. '
        try:
            email = validate_email(email).normalized
        except EmailNotValidError as error:
            return str(error)
        if await self.searchUserByEmail(email):
            return 'Email already exist. '
        
        password_hash = self.hasher.hash(password) if password else 'null'
        await self.db.execute('''
            INSERT INTO users(username, display_name, email, password_hash, status) VALUES ($1, $2, $3, $4, $5)
        ''', username, display_name, email, password_hash, status)

    async def createGame(self, name: str, display_name: str):
        await self.db.execute(f'''
            CREATE TABLE IF NOT EXISTS game_{name} (
                uid SERIAL PRIMARY KEY, 
                user_uid SERIAL, 
                replay_json json
            )
        ''')
        await self.db.execute('''
            INSERT INTO games(name, display_name) VALUES ($1, $2)
        ''', name, display_name)

    async def submitScore(self, gameName: str, userUID: int, replayJson: str):
        if not await self.searchUserByUid(userUID):
            return 'Invalid UID! '
        
        try:
            await self.db.execute(f'''
                INSERT INTO game_{gameName}(user_uid, replay_json) VALUES ($1, $2)
            ''', userUID, replayJson)
        except asyncpg.exceptions.UndefinedTableError:
            return 'Game not created! '
        except asyncpg.exceptions.InvalidTextRepresentationError:
            return 'Replay file must be in json format! '
