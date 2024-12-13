from aiohttp import web

routes = web.RouteTableDef()

@routes.get('/')
async def homePage(request: web.Request) -> web.Response:
    return web.Response(text="Score API Server")

@routes.post('/client/{game}/score/submit')
async def scoreSubmit(request: web.Request) -> web.Response:
    if not request.can_read_body:
        return web.Response(status=400, text='No Request Body Found! ')

    body = await request.json()
    
    return web.Response(text=f'{request.match_info['game']} {body['test']}')

@routes.get('/client/{game}/score/get')
async def scoreGet(request: web.Request) -> web.Response:
    return web.Response(text=f'{request.rel_url.query['id']}')

@routes.get('/client/{game}/score/leaderboard')
async def scoreLeaderBoard(request: web.Request) -> web.Response:
    return web.Response()

app = web.Application()
app.add_routes(routes)
web.run_app(app)
