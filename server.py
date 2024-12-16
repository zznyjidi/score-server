import asyncio
import json
from typing import Optional

from aiohttp import web

from database import PostgresDB

database: Optional[PostgresDB] = None
routes = web.RouteTableDef()

async def initDBifNotAlready():
    global database
    if not database:
        database = await PostgresDB("postgres://score-server:password@127.0.0.1:5432/scores")
    return database

@routes.get('/')
async def homePage(request: web.Request) -> web.Response:
    return web.Response(text="Score API Server")

@routes.post('/auth/user/new')
async def userNew(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    params = await request.post()
    status = await database.createUser(params.get('username'), params.get('nickname'), params.get('email'))
    return web.Response(status=status['status'], text=json.dumps(status))

@routes.post('/client/{game}/score/submit')
async def scoreSubmit(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    if not request.can_read_body:
        status = {
            "status": 400, 
            "message": "No Replay File! "
        }
    else:
        try:
            replay = await request.json()
            status = await database.submitScore(request.match_info['game'], int(request.rel_url.query['uid']), replay)
        except json.decoder.JSONDecodeError:
            status = {
                "status": 415, 
                "message": "Replay file must be in json format! "
            }
    return web.Response(status=status["status"], text=json.dumps(status))

@routes.get('/client/{game}/score/get')
async def scoreGet(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    try:
        result = await database.fetchScore(request.match_info['game'], int(request.rel_url.query['uid']))
    except ValueError:
        result = {
            "status": 400, 
            "message": "Invalid Replay UID! "
        }
    http_code = result.get('status', 200)
    return web.Response(status=http_code, text=json.dumps(result))

@routes.get('/client/{game}/score/leaderboard')
async def scoreLeaderBoard(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    try:
        result = await database.fetchLeaderBoard(request.match_info['game'], int(request.rel_url.query['level']))
    except ValueError:
        result = {
            "status": 400, 
            "message": "Invalid Level ID! "
        }
    http_code = 200 if isinstance(result, list) else result.get("status", 200)
    return web.Response(status=http_code, text=json.dumps(result))

app = web.Application()
app.add_routes(routes)
web.run_app(app)
