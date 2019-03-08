"""Recache Endpoint."""

import asyncio
import uvloop

from utils.logging import LOG
from utils.utils import clear_cache, get_services, db_get_service_urls, notify_service

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def recache_beacons(request, db_pool):
    """Delete local Beacon cache and request new information from Registry."""
    LOG.debug('Starting re-caching of Beacons.')

    await clear_cache()
    LOG.debug('Cache has been cleared.')

    services = await get_services(db_pool)  # re-caching happens here
    LOG.debug('Cache has been renewed.')
    LOG.debug(f'Cached Beacons: {services}')


async def remote_recache_aggregators(request, db_pool):
    """Send a request to Aggregators to renew their Beacon caches."""
    LOG.debug('Starting remote re-caching of Aggregators.')

        # Task variables
    params = request.query_string  # query parameters (variant search)
    tasks = []  # requests to be done
    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        services = await db_get_service_urls(connection, service_type='GA4GHBeaconAggregator')  # service urls (aggregators) to be queried

    for service in services:
        # Generate task queue
        task = asyncio.ensure_future(notify_service(service))
        tasks.append(task)

    # Prepare and initiate co-routines
    await asyncio.gather(*tasks)
