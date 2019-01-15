"""Common Services Endpoint."""

from aiohttp import web

from utils.logging import LOG
from utils.db_ops import db_check_service_id, db_register_service, db_get_service_details, db_delete_services, db_update_sequence
from utils.utils import query_params


async def register_service(request, db_pool):
    """Register a new service at host."""
    LOG.debug('Register new service.')
    # Get POST request body JSON as python dict
    service = await request.json()

    # Take connection from database pool, re-use connection for all tasks
    async with db_pool.acquire() as connection:
        # Check that the chosen service ID is not taken
        id_taken = await db_check_service_id(connection, service['id'])
        if id_taken:
            raise web.HTTPConflict(text='Service ID is taken.')
        # Register service to host
        await db_register_service(connection, service)

    return True


async def get_services(request, db_pool):
    """Return service details."""
    LOG.debug('Return services.')

    # Parse query params from path
    service_id, params = await query_params(request)

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        # Fetch services from database
        response = await db_get_service_details(connection,
                                                id=service_id,
                                                service_type=params.get('serviceType', None),
                                                api_version=params.get('apiVersion', None),
                                                list_format=params.get('listFormat', 'full'))

    return response


async def update_service(request, db_pool):
    """Update service details."""
    LOG.debug('Update service.')
    # Get POST request body JSON as python dict
    service = await request.json()

    # Parse query params from path, mainly service_id
    service_id, params = await query_params(request)

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        # If user gave service ID, start processes
        if service_id:
            # Verify that given service exists
            id_found_service = await db_check_service_id(connection, service_id)
            if not id_found_service:
                raise web.HTTPNotFound(text='No services found with given service ID.')
            # Service ID exists, initiate update sequence
            await db_update_sequence(connection, service_id, service)
        # User didn't give service ID in path -> 400 BadRequest
        else:
            raise web.HTTPBadRequest(text='Missing path parameter Service ID: "/services/<service_id>"')


async def delete_services(request, db_pool):
    """Delete service(s)."""
    LOG.debug('Delete service(s).')

    # Parse query params from path, mainly service_id
    service_id, params = await query_params(request)

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        # Delete specified service
        if service_id:
            # Verify that given service_id exists
            id_found = await db_check_service_id(connection, service_id)
            if not id_found:
                raise web.HTTPNotFound(text='No services found with given service ID.')
            await db_delete_services(connection, id=service_id)
        # Delete all services
        else:
            await db_delete_services(connection)