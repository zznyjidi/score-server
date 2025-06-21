from aiohttp import web

from server import server

if __name__ == '__main__':
    app = web.Application()
    app.add_routes(server.routes)
    web.run_app(app)
