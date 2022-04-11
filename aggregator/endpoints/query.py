"""Aggregator Query Endpoint."""

import asyncio
import uvloop

from aiohttp import web

from ..config import CONFIG
from ..utils.logging import LOG
from ..utils.utils import get_access_token, get_services, query_service, parse_results

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def send_beacon_query(request):
    """Send Beacon queries and respond synchronously."""
    LOG.debug("Normal response (sync).")

    tasks = []  # requests to be done
    services = await get_services(request.host)  # service urls (beacons, aggregators) to be queried
    access_token = await get_access_token(request)  # Get access token if one exists

    for service in services:
        # Generate task queue
        if "&filters=filter" in request.query_string:
            task = asyncio.ensure_future(query_service(service, request.query_string.replace("&filters=filter", ""), access_token))
            tasks.append(task)
            task = asyncio.ensure_future(query_service(service, "filter", access_token))
            tasks.append(task)
        else:
            task = asyncio.ensure_future(query_service(service, request.query_string, access_token))
            tasks.append(task)
    # Prepare and initiate co-routines
    results = await asyncio.gather(*tasks)

    # Check if this aggregator is aggregating aggregators
    # Aggregators return lists instead of objects, so they need to be broken down into a single list
    if CONFIG.aggregators:
        results = await parse_results(results)

    return results


async def send_beacon_query_websocket(request):
    """Send Beacon queries and respond asynchronously via websocket."""
    LOG.debug("Websocket response (async).")
    # Prepare websocket connection
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Task variables
    tasks = []  # requests to be done
    services = await get_services(request.host)  # service urls (beacons, aggregators) to be queried
    access_token = await get_access_token(request)  # Get access token if one exists

    for service in services:
        # Generate task queue
        LOG.debug(f"Query service: {service}")
        if "&filters=filter" in request.query_string:
            task = asyncio.ensure_future(query_service(service, request.query_string.replace("&filters=filter", ""), access_token, ws=ws))
            tasks.append(task)
            task = asyncio.ensure_future(query_service(service, "filter", access_token, ws=ws))
            tasks.append(task)
        else:
            task = asyncio.ensure_future(query_service(service, request.query_string, access_token, ws=ws))
            tasks.append(task)
    # Prepare and initiate co-routines
    await asyncio.gather(*tasks)
    # Close websocket after all results have been sent
    await ws.close()

    return ws
