"""Aggregator Query Endpoint."""

import asyncio
import uvloop

from aiohttp import web

from utils.logging import LOG
from utils.utils import get_access_token, get_services, query_service

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def send_beacon_query(request, db_pool):
    """Send Beacon queries and respond synchronously."""
    LOG.debug('Normal response (sync).')
    # response = web.Response()
    # await response.prepare(request)

    # Task variables
    params = request.query_string  # query parameters (variant search)
    tasks = []  # requests to be done
    services = await get_services(db_pool)  # service urls (beacons, aggregators) to be queried
    access_token = await get_access_token(request)  # Get access token if one exists

    for service in services:
        # Generate task queue
        task = asyncio.ensure_future(query_service(service, params, access_token))
        tasks.append(task)

    # Prepare and initiate co-routines
    results = await asyncio.gather(*tasks)

    return results


async def send_beacon_query_websocket(request, db_pool):
    """Send Beacon queries and respond asynchronously via websocket."""
    LOG.debug('Websocket response (async).')
    # Prepare websocket connection
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Task variables
    params = request.query_string  # query parameters (variant search)
    tasks = []  # requests to be done
    services = await get_services(db_pool)  # service urls (beacons, aggregators) to be queried
    access_token = await get_access_token(request)  # Get access token if one exists

    for service in services:
        # Generate task queue
        task = asyncio.ensure_future(query_service(service, params, access_token, ws=ws))
        tasks.append(task)

    # Prepare and initiate co-routines
    await asyncio.gather(*tasks)
    # Close websocket after all results have been sent
    await ws.close()

    return ws
