"""Recache Endpoint."""

from aiohttp import web

from utils.logging import LOG
from utils.utils import clear_cache, get_services


async def recache_beacons(request, db_pool):
    """Delete local Beacon cache and request new information from Registry."""
    LOG.debug('Starting re-caching of Beacons.')

    await clear_cache()
    LOG.debug('Cache has been cleared.')

    services = await get_services(db_pool)  # re-caching happens here
    LOG.debug('Cache has been renewed.')
    LOG.debug(f'Cached Beacons: {services}')
