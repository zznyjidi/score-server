import functools
import json
from typing import Any, Awaitable, Callable, Optional, Protocol

from aiohttp import web

from .setup import postgres_key, redis_key


class Response:
    status: int = 200
    message: str = ''
    body: Optional[dict[str, Any]] = None

    def __init__(self, 
            status: int = 200, 
            message: str = 'Success. ', 
            body: Optional[dict[str, Any]] = None
        ):
        self.status = status
        self.message = message
        self.body = body

    def to_json_respond(self) -> web.Response:
        response_body = {
            'status': self.status,
            'message': self.message,
        }
        if self.body:
            if isinstance(self.body, dict):
                response_body |= self.body
            else:
                response_body['payload'] = self.body
        return web.json_response(
            response_body, 
            status=self.status
        )

class RequestProcessor(Protocol):
    def __call__(self, request: web.Request, *args: Any, **kwds: Any) -> Awaitable[Response]:
        ...

async def extract_params(
        request: web.Request, *,
        query_param: Optional[list[str]] = None,
        body_param: Optional[list[str]] = None,
        url_match: Optional[list[str]] = None
    ) -> dict[str, Any]:
    """Extract Parameters from a aiohttp request object

    Args:
        request (web.Request): request object
        query_param (list[str], optional): list of query parameters to parse. Defaults to None.
        body_param (list[str], optional): list of parameters extracts from the json body. Defaults to None.
        url_match (list[str], optional): list of parameters from the url variables. Defaults to None.

    Raises:
        web.HTTPBadRequest: when requested parameter is not found

    Returns:
        dict[str, Any]: parsed parameters dict
    """

    params: dict[str, Any] = {}

    if query_param:
        rel_url = request.rel_url
        for param in query_param:
            try:
                params[param] = rel_url.query[param]
            except KeyError as e:
                raise web.HTTPBadRequest(
                    content_type="application/json", 
                    text=json.dumps({
                        "status": 400,
                        "message": f"Missing parameter: {str(e)}! "
                    })
                ) from e

    if body_param:
        try:
            body = await request.json()
            for param in body_param:
                value = body[param]
                params[param] = value
        except KeyError as e:
            raise web.HTTPBadRequest(
                content_type="application/json",
                text=json.dumps({
                        "status": 400,
                        "message": f"Missing payload: {str(e)}! "
                })
            ) from e
        except json.decoder.JSONDecodeError as e:
            raise web.HTTPBadRequest(
                content_type="application/json",
                text=json.dumps({
                        "status": 400,
                        "message": "Invalid request body! "
                })
            ) from e

    if url_match:
        for param in url_match:
            params[param] = request.match_info[param]

    return params

def request_to_params(
        query_param: Optional[list[str]] = None,
        body_param: Optional[list[str]] = None,
        url_match: Optional[list[str]] = None
    ):
    """Parse request parameters from the request and put them into the function parameters

    Args:
        query_param (Optional[list[str]], optional): list of query parameters to parse. Defaults to None.
        body_param (Optional[list[str]], optional): list of parameters extracts from the json body. Defaults to None.
        url_match (Optional[list[str]], optional): list of parameters from the url variables. Defaults to None.
    """
    def decorator(func: RequestProcessor) -> Callable[[web.Request], Awaitable[web.Response]]:
        @functools.wraps(func)
        async def wrapper(request: web.Request, *args, **kwargs) -> web.Response:
            params = await extract_params(
                request, 
                query_param=query_param, 
                body_param=body_param, 
                url_match=url_match
            )
            result = await func(request, *args, **kwargs, **params)
            return result.to_json_respond()
        return wrapper
    return decorator

def with_database(func: RequestProcessor) -> RequestProcessor:
    @functools.wraps(func)
    async def wrapper(request: web.Request, *args, **kwargs) -> Response:
        return await func(request, *args, **kwargs, database=request.app[postgres_key])
    return wrapper

def with_cache(func: RequestProcessor) -> RequestProcessor:
    @functools.wraps(func)
    async def wrapper(request: web.Request, *args, **kwargs) -> Response:
        return await func(request, *args, **kwargs, cache=request.app[redis_key])
    return wrapper
