import json
import os
from typing import Optional

from aiohttp import web

from . import preprocess
from .database import PostgresDB

database: Optional[PostgresDB] = None
routes = web.RouteTableDef()

async def initDBifNotAlready():
    global database
    if not database:
        database = await PostgresDB(
            host=os.getenv("POSTGRES_HOST", "127.0.0.1"), 
            port=os.getenv("POSTGRES_PORT", 5432), 
            user=os.getenv("POSTGRES_USER", "score-server"),
            password=os.getenv("POSTGRES_PASS", "password"), 
            database=os.getenv("POSTGRES_DB", "scores")
        )
    return database

@routes.get('/')
async def homePage(request: web.Request) -> web.Response:
    return web.Response(text="Score API Server")

@routes.post('/auth/user/new')
@preprocess.request_to_params(body_param=['username', 'nickname', 'email'])
async def userNew(username: str, nickname: str, email: str) -> preprocess.Response:
    database = await initDBifNotAlready()
    status = await database.createUser(username, nickname, email)
    return preprocess.Response(status=status['status'], body=status)

@routes.post('/auth/client/login')
@preprocess.request_to_params(body_param=['username', 'password'])
async def clientLogin(request: web.Request, username: str, password: str) -> preprocess.Response:
    database = await initDBifNotAlready()
    uid, nickname = await database.authenticateUser(username, password)
    if (uid) > 0:
        status = {
            "status": 200, 
            "message": "Success. User Verified. ",
            "uid": uid, 
            "nickname": nickname
        }
    else:
        match uid:
            case -1:
                status = {
                    "status": 403, 
                    "message": "Invalid Username or Password! "
                }
            case -2:
                status = {
                    "status": 401, 
                    "message": "User not active or password not set! "
                }
            case _:
                assert False
    return preprocess.Response(status=status["status"], message=status["message"], body=status)

@routes.post('/client/{game}/score/submit')
@preprocess.request_to_params(url_match=['game'], query_param=['uid'], body_param=['replay'])
async def scoreSubmit(request: web.Request, game: str, uid: str, replay: str) -> preprocess.Response:
    database = await initDBifNotAlready()
    try:
        replay_json = json.loads(replay)
        status = await database.submitScore(game, int(uid), replay_json)
    except json.decoder.JSONDecodeError:
        status = {
            "status": 415, 
            "message": "Replay file must be in json format! "
        }
    return preprocess.Response(status=status["status"], message=status["message"], body=status)

@routes.get('/client/{game}/score/get')
@preprocess.request_to_params(url_match=['game'], query_param=['uid'])
async def scoreGet(request: web.Request, game: str, uid: str) -> preprocess.Response:
    database = await initDBifNotAlready()
    try:
        result = await database.fetchScore(game, int(uid))
    except ValueError:
        result = {
            "status": 400, 
            "message": "Invalid Replay UID! "
        }
    http_code:int = result.get('status', 200)
    return preprocess.Response(status=http_code, body=result)

@routes.get('/client/{game}/score/leaderboard')
@preprocess.request_to_params(url_match=['game'], query_param=['level'])
async def scoreLeaderBoard(request: web.Request, game: str, level: str) -> preprocess.Response:
    database = await initDBifNotAlready()
    try:
        result = await database.fetchLeaderBoard(game, int(level))
    except ValueError:
        result = {
            "status": 400, 
            "message": "Invalid Level ID! "
        }
    http_code = 200 if isinstance(result, list) else result.get("status", 200)
    return preprocess.Response(status=http_code, body=result)
