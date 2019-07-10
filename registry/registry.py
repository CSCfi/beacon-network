"""Beacon Registry API."""

import sys
import json

import aiohttp_cors

from aiohttp import web

from .endpoints.info import get_info
from .endpoints.service_types import get_service_types
# from .endpoints.services import register_service, get_services, update_service, delete_services
from .endpoints.services import register_service, get_services, update_service
from .schemas import load_schema
from .utils.utils import invalidate_aggregator_caches, application_security
from .utils.validate import validate, api_key
from .utils.db_pool import init_db_pool
from .utils.logging import LOG
from .config import CONFIG

routes = web.RouteTableDef()


@routes.get('/', name='index')
async def index(request):
    """Greeting endpoint.

    Returns name of the service, doubles as a healthcheck utility."""
    LOG.debug('Greeting endpoint.')
    return web.Response(text=CONFIG.name)


@routes.get('/service-info')
async def info(request):
    """Return service info."""
    LOG.debug('GET /info received.')
    return web.json_response(await get_info(request.host))


@routes.get('/services/types')
async def service_types(request):
    """Return service types."""
    LOG.debug('GET /services/types received.')
    return web.json_response(await get_service_types())


@routes.post('/services')
@validate(load_schema("self_registration"))
async def services_post(request):
    """POST request to the /services endpoint.
    Register a new service at host.
    """
    LOG.debug('POST /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    response = await register_service(request, db_pool)

    # Notify aggregators of changed service catalogue
    # await invalidate_aggregator_caches(request, db_pool)

    # Return confirmation and service key if no problems occurred during processing
    return web.HTTPCreated(body=json.dumps(response), content_type='application/json')


@routes.get('/services')
@routes.get('/services/{service_id}')
async def services_get(request):
    """GET request to the /services endpoint.
    Return services that are registered at host.
    """
    LOG.debug('GET /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    response = await get_services(request, db_pool)

    # Return results
    return web.json_response(response)


@routes.put('/services/{service_id}')
@validate(load_schema("self_registration"))
async def services_put(request):
    """PATCH request to the /user endpoint.
    Update service details at host.
    """
    LOG.debug('PUT /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    await update_service(request, db_pool)

    # # Notify aggregators of changed service catalogue
    # await invalidate_aggregator_caches(request, db_pool)

    # Return confirmation
    return web.Response(text='Service has been updated.')


# @routes.delete('/services')
# @routes.delete('/services/{service_id}')
# async def services_delete(request):
#     """DELETE request to the /user endpoint.
#     Delete registered service from host.
#     """
#     LOG.debug('DELETE /services received.')
#     # Tap into the database pool
#     db_pool = request.app['pool']

#     # Send request for processing
#     await delete_services(request, db_pool)

#     # Notify aggregators of changed service catalogue
#     await invalidate_aggregator_caches(request, db_pool)

#     # Return confirmation
#     return web.HTTPNoContent()


async def init_db(app):
    """Initialise a database connection pool."""
    LOG.info('Creating database connection pool.')
    app['pool'] = await init_db_pool(host=CONFIG.db_host,
                                     port=CONFIG.db_port,
                                     user=CONFIG.db_user,
                                     passwd=CONFIG.db_pass,
                                     db=CONFIG.db_name)


async def close_db(app):
    """Close the database connection pool."""
    LOG.info('Closing database connection pool.')
    await app['pool'].close()


def set_cors(app):
    """Set CORS rules."""
    LOG.debug('Applying CORS rules.')
    # Configure CORS settings, allow all domains
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    # Apply CORS to endpoints
    for route in list(app.router.routes()):
        cors.add(route)


def init_app():
    """Initialise the web server."""
    LOG.info('Initialising web server.')
    app = web.Application(middlewares=[api_key()])
    app.router.add_routes(routes)
    set_cors(app)
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)
    return app


def main():
    """Run the web server."""
    LOG.info('Starting server build.')
    web.run_app(init_app(),
                host=CONFIG.host,
                port=CONFIG.port,
                shutdown_timeout=0,
                ssl_context=application_security())


if __name__ == '__main__':
    if sys.version_info < (3, 6):
        LOG.error("beacon-network:registry requires python 3.6 or higher")
        sys.exit(1)
    main()
