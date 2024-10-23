from aiohttp.web_request import Request
from aiohttp.web_response import json_response


async def test_handler(request: Request):
    return json_response({"webhook": "Hello, World!"}, status=200)
