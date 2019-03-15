"""Recache Endpoint."""

import asyncio

import uvloop


from utils.logging import LOG
from utils.utils import clear_cache, cache_from_registry

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def recache_beacons(request, db_pool):
    """Delete local Beacon cache and request new information from Registry."""
    LOG.debug('Starting re-caching of Beacons.')
    # Get POST request body JSON as python dict
    beacons = await request.json()

    response = await clear_cache()
    LOG.debug('Cache has been cleared.')

    response = await cache_from_registry(beacons, response)  # re-caching happens here
    LOG.debug('Cache has been renewed.')

    return response
