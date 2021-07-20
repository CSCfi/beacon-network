"""Validation Utilities."""

from aiohttp import web

from .utils import validate_service_key
from .logging import LOG


def api_key():
    """Check if API key is valid."""
    LOG.debug("Validate API key.")

    @web.middleware
    async def api_key_middleware(request, handler):
        LOG.debug("Start API key check")

        if not isinstance(request, web.Request):
            raise web.HTTPBadRequest(text="Invalid HTTP Request.")

        # This is the only endpoint which requires authentication
        if "/cache" in request.path:
            LOG.debug("At /cache endpoint.")
            try:
                service_key = request.headers["Authorization"]
                LOG.debug("Authorization received.")
            except Exception:
                LOG.debug('Missing "Authorization" from headers.')
                raise web.HTTPBadRequest(text='Missing header "Authorization".')
            # Validate service key
            await validate_service_key(service_key)
            # None of the checks failed
            return await handler(request)

        # For all other endpoints
        else:
            LOG.debug("No API key required at this endpoint.")
            return await handler(request)

    return api_key_middleware
