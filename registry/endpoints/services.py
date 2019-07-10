"""Common Services Endpoint."""

from aiohttp import web

from ..config import CONFIG
from ..utils.logging import LOG
# from ..utils.db_ops import db_check_service_id, db_register_service, db_get_service_details, db_delete_services, db_update_sequence
from ..utils.db_ops import db_check_service_id, db_register_service, db_get_service_details, db_update_sequence
from ..utils.utils import http_request_info, generate_service_id, parse_service_info, query_params


async def register_service(request, db_pool):
    """Register a new service at host."""
    LOG.debug('Register new service.')
    # Get POST request body JSON as python dict
    r = await request.json()
    url = r.get('url')

    # Response object
    response = {'message': '',
                'serviceId': '',
                'serviceKey': '',
                'help': CONFIG.documentation_url}

    # Request service info from given url
    service_info = await http_request_info(url)

    # Generate id from given url
    # Note that we don't use the ID provided by the service itself, but instead
    # generate a unique ID for them, based on their domain (in reverse notation)
    service_id = await generate_service_id(url)

    # Take connection from database pool, re-use connection for all tasks
    async with db_pool.acquire() as connection:
        # Check that the chosen service ID is not taken
        id_taken = await db_check_service_id(connection, service_id)
        if id_taken:
            raise web.HTTPConflict(text=f'Service ID "{service_id}" is taken.')
        # Parse and validate service info object
        service = await parse_service_info(service_id, r, service_info)
        # Register service to host
        service_key = await db_register_service(connection, service, r['email'])
        if r['type'] in ['urn:ga4gh:beacon', 'urn:ga4gh:registry']:
            response['message'] = 'Service has been registered. Service key and id for updating and deleting'\
                                  'registration included in this response, keep them safe.'
        elif r['type'] == 'urn:ga4gh:aggregator':
            response['message'] = 'Service has been registered. Service key and id for updating and deleting'\
                                  'registration included in this response, keep them safe. Add this key to'\
                                  '`registries.json` to allow this Registry to invalidate the cached Beacons'\
                                  'at your Aggregator in case of catalogue changes.'
        response['serviceId'] = service_id
        response['serviceKey'] = service_key

    return response


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
                                                service_type=params.get('type', None),
                                                api_version=params.get('apiVersion', None))

    return response


async def update_service(request, db_pool):
    """Update service details."""
    LOG.debug('Update service.')
    # Get POST request body JSON as python dict
    r = await request.json()
    url = r.get('url')

    # Parse query params from path, mainly service_id
    service_id, _ = await query_params(request)

    # Check that user specified id in path
    if service_id:
        # Take connection from the database pool
        async with db_pool.acquire() as connection:
            # Verify that given service exists
            id_found_service = await db_check_service_id(connection, service_id)
            if not id_found_service:
                raise web.HTTPNotFound(text='No services found with given service ID.')
            # Request service info from given url and generate a new ID in case it changed
            service_info = await http_request_info(url)
            service_id = await generate_service_id(url)
            # Parse and validate service info object
            service = await parse_service_info(service_id, r, service_info)
            # Initiate update
            await db_update_sequence(connection, service_id, service, r['email'])
    else:
        raise web.HTTPBadRequest(text='Missing path parameter Service ID: "/services/<service_id>"')


# async def delete_services(request, db_pool):
#     """Delete service(s)."""
#     LOG.debug('Delete service(s).')

#     # Parse query params from path, mainly service_id
#     service_id, params = await query_params(request)

#     # Delete specified service
#     if service_id:
#         # Take connection from the database pool
#         async with db_pool.acquire() as connection:
#             # # Delete specified service
#             # if service_id:
#             # Verify that given service_id exists
#             id_found = await db_check_service_id(connection, service_id)
#             if not id_found:
#                 raise web.HTTPNotFound(text='No services found with given service ID.')
#             await db_delete_services(connection, id=service_id)
#             # # Delete all services
#             # else:
#             #     await db_delete_services(connection)
#     else:
#         raise web.HTTPForbidden(text='Mass deletion has been disabled.')
