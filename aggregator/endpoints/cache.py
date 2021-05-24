"""Recache Endpoint."""

import asyncio

import uvloop


from ..utils.logging import LOG
from ..utils.utils import clear_cache

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def invalidate_cache():
    """Delete local Beacon cache."""
    LOG.debug("Invalidate cached Beacons.")

    await clear_cache()
    LOG.debug("Cache invalidating procedure complete.")
