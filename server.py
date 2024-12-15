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
    if status:
        return web.Response(status=400, text=status)
    else:
        return web.Response(text='Success')

@routes.post('/client/{game}/score/submit')
async def scoreSubmit(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    if not request.can_read_body:
        return web.Response(status=400, text='No Request Body! ')

    body = await request.json()
    replay = json.dumps(body, indent=-1)
    replay = replay.replace('\r', '').replace('\n', '')
    
    status = await database.submitScore(request.match_info['game'], int(request.rel_url.query['uid']), replay)
    if status:
        return web.Response(status=400, text=status)
    else:
        return web.Response(text='Success')

@routes.get('/client/{game}/score/get')
async def scoreGet(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    return web.Response(text=f'{request.rel_url.query['id']}')

@routes.get('/client/{game}/score/leaderboard')
async def scoreLeaderBoard(request: web.Request) -> web.Response:
    database = await initDBifNotAlready()
    return web.Response()

app = web.Application()
app.add_routes(routes)
web.run_app(app)
