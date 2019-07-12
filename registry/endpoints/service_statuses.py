"""Service Statuses Endpoint."""

from aiohttp import web

from ..utils.logging import LOG


async def get_service_statuses():
    """Return GA4GH service types."""
    LOG.debug('Check service statuses.')
    raise web.HTTPNotImplemented()
