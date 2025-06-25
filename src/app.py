import sys
from aiohttp import web

from server import server, setup

if __name__ == '__main__':
    app = web.Application()

    app[setup.config_key] = setup.parse_config(sys.argv)

    app.cleanup_ctx.append(setup.init_database)
    app.cleanup_ctx.append(setup.init_cache)

    app.add_routes(server.routes)

    web.run_app(app)
