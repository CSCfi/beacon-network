"""Beacon Aggregator API."""

import sys

import aiohttp_cors

from aiohttp import web

from .endpoints.info import get_info
from .endpoints.query import send_beacon_query, post_beacon_query, send_beacon_query_websocket
from .endpoints.cache import invalidate_cache
from .utils.utils import application_security
from .utils.validate import api_key
from .utils.logging import LOG
from .config import CONFIG

routes = web.RouteTableDef()


@routes.get("/", name="index")
async def index(request):
    """Greeting endpoint.

    Returns name of the service, doubles as a healthcheck utility.
    """
    LOG.debug("Greeting endpoint.")
    return web.Response(text=CONFIG.name)


@routes.get("/service-info")
async def info(request):
    """Return service info."""
    LOG.debug("GET /info received.")
    return web.json_response(await get_info(request.host))


@routes.get("/query")
async def query(request):
    """Forward variant query to Beacons."""
    LOG.debug("GET /query received.")

    # For websocket
    connection_header = request.headers.get("Connection", "default").lower().split(",")  # break down if multiple items
    connection_header = [value.strip() for value in connection_header]  # strip spaces

    if "upgrade" in connection_header and request.headers.get("Upgrade", "default").lower() == "websocket":
        # Use asynchronous websocket connection
        # Send request for processing
        websocket = await send_beacon_query_websocket(request)

        # Return websocket connection
        return websocket
    else:
        # Use standard synchronous http
        # Send request for processing
        LOG.info("Use standard synchronous http. Send request for processing")
        response = await send_beacon_query(request)

        # Return results
        return web.json_response(response)


@routes.post("/query1")
async def query1(request):
    """Forward variant query to Beacons."""
    LOG.debug("POST /query received.")

    # For websocket
    connection_header = request.headers.get("Connection", "default").lower().split(",")  # break down if multiple items
    connection_header = [value.strip() for value in connection_header]  # strip spaces

    if "upgrade" in connection_header and request.headers.get("Upgrade", "default").lower() == "websocket":
        # Use asynchronous websocket connection
        # Send request for processing
        websocket = await post_beacon_query(request)

        # Return websocket connection
        return websocket
    else:
        # Use standard synchronous http
        # Send request for processing
        LOG.info("Use standard synchronous http. Send request for processing --- sending post_beacon_query neeew"+str(request.headers))
        response = await post_beacon_query(request)

        # Return results
        return web.json_response(response)



@routes.delete("/cache")
async def cache(request):
    """Invalidate cached Beacons."""
    LOG.debug("DELETE /beacons received.")

    # Send request for processing
    await invalidate_cache()

    # Return confirmation
    return web.Response(text="Cache has been deleted.")


def set_cors(app):
    """Set CORS rules."""
    LOG.debug(f"Applying CORS rules: {CONFIG.cors}.")
    # Configure CORS settings, allow all domains
    cors = aiohttp_cors.setup(
        app,
        defaults={
            CONFIG.cors: aiohttp_cors.ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
            )
        },
    )
    # Apply CORS to endpoints
    for route in list(app.router.routes()):
        cors.add(route)


async def init_app():
    """Initialise the web server."""
    LOG.info("Initialising web server.")
    app = web.Application(middlewares=[api_key()])
    app.router.add_routes(routes)
    if CONFIG.cors:
        set_cors(app)
    return app


def main():
    """Run the web server."""
    LOG.info("Starting server build.")
    web.run_app(init_app(), host=CONFIG.host, port=CONFIG.port, shutdown_timeout=0, ssl_context=application_security())


if __name__ == "__main__":
    if sys.version_info < (3, 6):
        LOG.error("beacon-network:aggregator requires python 3.6 or higher")
        sys.exit(1)
    main()
