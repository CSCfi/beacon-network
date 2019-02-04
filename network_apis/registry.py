"""Beacon Registry API."""

import os
import sys

import aiohttp_cors

from aiohttp import web

from endpoints.info import get_info
from endpoints.service_types import get_service_types
from endpoints.services import register_service, get_services, update_service, delete_services
from schemas import load_schema
from utils.validate import validate
from utils.db_pool import init_db_pool
from utils.logging import LOG
from config import CONFIG

routes = web.RouteTableDef()


@routes.get('/', name='index')
async def index(request):
    """Greeting endpoint."""
    LOG.debug('Greeting endpoint.')
    return web.Response(text='GA4GH Beacon Registry API')


@routes.get('/info')
async def info(request):
    """Return service info."""
    LOG.debug('GET /info received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    response = await get_info(CONFIG.registry['host_id'], db_pool)

    # Return results
    return web.json_response(response)


@routes.get('/servicetypes')
async def service_types(request):
    """Return service types."""
    LOG.debug('GET /servicetypes received.')
    response = await get_service_types()
    return web.json_response(response)


@routes.post('/services')
@validate(load_schema("serviceinfo"))
async def services_post(request):
    """POST request to the /services endpoint.
    Register a new service at host.
    """
    LOG.debug('POST /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    service_key = await register_service(request, db_pool)

    # Return confirmation and service key if no problems occurred during processing
    return web.HTTPCreated(text=f'Service has been registered. Service key for updating and deleting registration, keep it safe: {service_key}')


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
@validate(load_schema("serviceinfo"))
async def services_put(request):
    """PATCH request to the /user endpoint.
    Update service details at host.
    """
    LOG.debug('PUT /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    await update_service(request, db_pool)

    # Return confirmation
    return web.HTTPNoContent()


@routes.delete('/services')
@routes.delete('/services/{service_id}')
async def services_delete(request):
    """DELETE request to the /user endpoint.
    Delete registered service from host.
    """
    LOG.debug('DELETE /services received.')
    # Tap into the database pool
    db_pool = request.app['pool']

    # Send request for processing
    await delete_services(request, db_pool)

    # Return confirmation
    return web.HTTPNoContent()


async def init_db(app):
    """Initialise a database connection pool."""
    LOG.info('Creating database connection pool.')
    app['pool'] = await init_db_pool(host=os.environ.get('DB_HOST', CONFIG.registry.get('db_host', 'localhost')),
                                     port=os.environ.get('DB_PORT', CONFIG.registry.get('db_port', '5432')),
                                     user=os.environ.get('DB_USER', CONFIG.registry.get('db_user', 'user')),
                                     passwd=os.environ.get('DB_PASS', CONFIG.registry.get('db_pass', 'pass')),
                                     db=os.environ.get('DB_NAME', CONFIG.registry.get('db_name', 'db')))


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
    app = web.Application()
    app.router.add_routes(routes)
    set_cors(app)
    app.on_startup.append(init_db)
    app.on_cleanup.append(close_db)
    return app


def main():
    """Run the web server."""
    LOG.info('Starting server build.')
    web.run_app(init_app(),
                host=os.environ.get('APP_HOST', CONFIG.registry.get('app_host', '0.0.0.0')),
                port=os.environ.get('APP_PORT', CONFIG.registry.get('app_port', '8080')),
                shutdown_timeout=0)


if __name__ == '__main__':
    assert sys.version_info >= (3, 6), "This service requires python3.6 or above"
    LOG.info('Starting web server start-up routines.')
    main()
