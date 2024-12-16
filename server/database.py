import json
from enum import StrEnum
from typing import Optional, TypeAlias

import asyncpg
import asyncpg.prepared_stmt
from argon2 import PasswordHasher
from argon2 import exceptions as argon2Excepts
from email_validator import EmailNotValidError, validate_email

import replay

JSON: TypeAlias = dict[str, "JSON"] | list["JSON"] | str | int | float | bool | None

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
            self.fetchGames: asyncpg.prepared_stmt.PreparedStatement = await self.db.prepare('SELECT * FROM games')
            self.fetchScoreByGame: dict[str, asyncpg.prepared_stmt.PreparedStatement] = {}
            self.fetchScoreLeaderboard: dict[str, asyncpg.prepared_stmt.PreparedStatement] = {}
            for game in await self.fetchGames.fetch():
                self.fetchScoreByGame[game['name']] = await self.db.prepare(f'SELECT * FROM game_{game['name']} WHERE uid = $1')
                self.fetchScoreByGame[f"{game['name']}_json"] = await self.db.prepare(f'SELECT * FROM game_{game['name']} WHERE replay_json::jsonb @> $1::jsonb AND replay_json::jsonb <@ $1::jsonb')
                self.fetchScoreLeaderboard[game['name']] = await self.db.prepare(f'''
                    SELECT * FROM game_{game['name']}
                    WHERE CAST(replay_json -> 'info' ->> 'level_id' AS INTEGER) = $1
                    ORDER BY (replay_json -> 'info' ->> 'time')::integer ASC LIMIT 50
                ''')
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
                uid SERIAL NOT NULL PRIMARY KEY, 
                username text NOT NULL,
                email text NOT NULL,
                display_name text NOT NULL,
                password_hash text NOT NULL, 
                status user_status NOT NULL
            )
        ''')

        # Create games table
        await self.db.execute('''
            CREATE TABLE IF NOT EXISTS games (
                uid SERIAL NOT NULL PRIMARY KEY, 
                name text NOT NULL,
                display_name text NOT NULL
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

    async def createUser(self, username: str, display_name: str, email: str, *, password: str = None, status: userStatus = 'unverified') -> JSON:
        """### Create User in db

        Args:
            username (str): username
            display_name (str): nickname
            email (str): email
            password (str, optional): password. Defaults to None.
            status (userStatus, optional): status of the user. Defaults to 'unverified'.

        Returns:
            JSON: operation status
        """
        if not username:
            return {
                "status": 400, 
                "message": "Username can't be empty! "
            }
        if not display_name:
            return {
                "status": 400,
                "message": "Nickname can't be empty! "
            }
        if not email:
            return {
                "status": 400,
                "message": "Email cat't be empty! "
            }
        if await self.searchUserByUsername(username):
            return {
                "status": 400,
                "message": "Username already exist. "
            }
        if await self.searchUserByNickname(display_name):
            return {
                "status": 400, 
                "message": "Nickname already exist. "
            }
        try:
            email = validate_email(email).normalized
        except EmailNotValidError as error:
            return {
                "status": 400, 
                "message": f"Invalid Email: {str(error)}"
            }
        if await self.searchUserByEmail(email):
            return {
                "status": 400, 
                "message": "Email already exist. "
            }

        password_hash = self.hasher.hash(password) if password else 'null'
        await self.db.execute('''
            INSERT INTO users(username, display_name, email, password_hash, status) VALUES ($1, $2, $3, $4, $5)
        ''', username, display_name, email, password_hash, status)
        return {
            "status": 200, 
            "message": "Success, User Created. "
        }

    async def modifyUser(self, uid: int, *, email: str = None, password: str = None, status: userStatus = None) -> JSON:
        if not await self.searchUserByUid(uid):
            return {
                "status": 400, 
                "message": "Invalid UID! "
            }
        if (not email) and (not password) and (not status):
            return {
                "status": 400, 
                "message": "No Info Provided! "
            }

        if email:
            try:
                email = validate_email(email).normalized
            except EmailNotValidError as error:
                return {
                    "status": 400, 
                    "message": f"Invalid Email: {str(error)}"
                }
            if await self.searchUserByEmail(email):
                return {
                    "status": 400, 
                    "message": "Email already exist. "
                }
            await self.db.execute('''
                UPDATE users SET email = $1 WHERE uid = $2
            ''', email, uid)
        if password:
            password_hash = self.hasher.hash(password)
            await self.db.execute('''
                UPDATE users SET password_hash = $1 WHERE uid = $2
            ''', password_hash, uid)
        if status:
            await self.db.execute('''
                UPDATE users SET status = $1 WHERE uid = $2
            ''', status, uid)
        return {
            "status": 200, 
            "message": "Success, User Updated. "
        }

    async def authenticateUser(self, username: str, password: str) -> int:
        """### Get User UID from it's username and password

        Args:
            username (str): user's username
            password (str): user's password

        Returns:
            int: user's uid if positive 
            (-1: invalid login info, -2: user password not set)
        """
        if user_entry := (await self.searchUserByUsername(username)):
            user_entry = user_entry[0]
        else:
            return -1
        password_hash: str = user_entry['password_hash']
        try:
            if self.hasher.verify(password_hash, password):
                if self.hasher.check_needs_rehash:
                    await self.modifyUser(user_entry['uid'], password=password)
                return user_entry['uid']
            else:
                return -1
        except argon2Excepts.VerifyMismatchError:
            return -1
        except argon2Excepts.InvalidHashError:
            return -2

    async def createGame(self, name: str, display_name: str):
        await self.db.execute(f'''
            CREATE TABLE IF NOT EXISTS game_{name} (
                uid SERIAL NOT NULL PRIMARY KEY,
                user_uid SERIAL NOT NULL,
                replay_json json NOT NULL
            )
        ''')
        await self.db.execute('''
            INSERT INTO games(name, display_name) VALUES ($1, $2)
        ''', name, display_name)
        self.fetchScoreByGame[name] = self.db.prepare(f'SELECT * FROM game_{name} WHERE uid = $1')
        self.fetchScoreByGame[f"{name}_json"] = await self.db.prepare(f'SELECT * FROM game_{name} WHERE replay_json::jsonb @> $1::jsonb AND replay_json::jsonb <@ $1::jsonb')
        self.fetchScoreLeaderboard[name] = await self.db.prepare(f'''
            SELECT * FROM game_{name}
            WHERE CAST(replay_json -> 'info' ->> 'level_id' AS INTEGER) = $1
            ORDER BY (replay_json -> 'info' ->> 'time')::integer ASC LIMIT 50
        ''')

    async def submitScore(self, gameName: str, userUID: int, replayJson: JSON) -> JSON:
        if not replay.validateReplayJson(replayJson):
            return {
                "status": 400, 
                "message": "Invalid Replay File! "
            }
        if not await self.searchUserByUid(userUID):
            return {
                "status": 400, 
                "message": "Invalid UID! "
            }

        try:
            replayJson = json.dumps(replayJson)
            if fetched_result := await self.fetchScoreByGame[f"{gameName}_json"].fetch(replayJson):
                return  {
                    "status": 400, 
                    "message": "Replay File already submitted! ",
                    "replay_uid": fetched_result[0]['uid']
                }
            await self.db.execute(f'''
                INSERT INTO game_{gameName}(user_uid, replay_json) VALUES ($1, $2)
            ''', userUID, replayJson)
            return {
                "status": 200, 
                "message": "Success, Score Submitted. ", 
                "replay_uid": (await self.fetchScoreByGame[f"{gameName}_json"].fetch(replayJson))[0]['uid']
            }
        except (asyncpg.exceptions.UndefinedTableError, KeyError):
            return {
                "status": 400, 
                "message": "Invalid Game! "
            }
        except (asyncpg.exceptions.InvalidTextRepresentationError, json.decoder.JSONDecodeError):
            return {
                "status": 415, 
                "message": "Replay file must be in json format! "
            }

    async def fetchScore(self, gameName: str, replayUid: int) -> JSON:
        if result := await self.fetchScoreByGame[gameName].fetch(replayUid):
            return json.loads(result[0]['replay_json'])
        else:
            return {
                "status": 400, 
                "message": "Invalid Replay UID! "
            }

    async def fetchLeaderBoard(self, gameName: str, level: int) -> JSON:
        try:
            leaderboard: list[asyncpg.Record] = await self.fetchScoreLeaderboard[gameName].fetch(level)
            return [json.loads(replay["replay_json"]) for replay in leaderboard]
        except KeyError:
            return {
                "status": 400, 
                "message": "Invalid Game! "
            }
