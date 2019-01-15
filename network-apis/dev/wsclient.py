"""Dev Tools: Test Websocket."""

import asyncio
import os

import aiohttp

HOST = os.getenv('AGG_APP_HOST', 'localhost')
PORT = int(os.getenv('AGG_APP_PORT', 3001))

URL = f'ws://{HOST}:{PORT}/query'


async def main():
    session = aiohttp.ClientSession()
    async with session.ws_connect(URL) as ws:
        async for msg in ws:
            print(msg)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
