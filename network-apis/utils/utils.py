"""Small General-Purpose Utility Functions."""

import os
import json

import aiohttp

from aiohttp import web

from .logging import LOG
from .db_ops import db_get_service_urls


async def query_params(request):
    """Parse query string params from path."""
    LOG.debug('Parse query params.')
    # Query string params
    allowed_params = ['serviceType', 'model', 'listFormat', 'apiVersion']
    params = {k: v for k, v in request.rel_url.query.items() if k in allowed_params}
    # Path param
    service_id = request.match_info.get('service_id', None)
    return service_id, params


async def get_access_token(request):
    """Retrieve access token if it exists."""
    LOG.debug('Look for access token.')
    access_token = None

    if 'Authorization' in request.headers:
        LOG.debug('Auth from headers.')
        # First check if access token was delivered via headers
        auth_scheme, access_token = request.headers.get('Authorization').split(' ')
        if not auth_scheme == 'Bearer':
            LOG.debug(f'User tried to use "{auth_scheme}"" auth_scheme.')
            web.HTTPForbidden(text=f'Unallowed authorization scheme "{auth_scheme}", user "Bearer" instead.')
    elif 'access_token' in request.cookies:
        LOG.debug('Auth from cookies.')
        # Then check if access token was stored in cookies
        access_token = request.cookies.get('access_token')
    else:
        LOG.debug('No auth.')
        # Otherwise send nothing
        pass

    return access_token


async def get_services(db_pool):
    """Return service urls."""
    LOG.debug('Fetch service urls.')

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        services = await db_get_service_urls(connection)  # service urls (beacons, aggregators) to be queried

    return services


async def query_service(service, params, access_token, ws=None):
    """Query service with params."""
    LOG.debug('Querying service.')
    headers = {}

    if access_token:
        headers.update({f'Authorization: Bearer {access_token}'})

    # Query service in a session
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(service,
                                   params=params,
                                   ssl=os.environ.get('HTTPS_ONLY', False),
                                   headers=headers) as response:
                LOG.debug(response)
                # On successful response, forward response
                if response.status == 200:
                    result = await response.json()
                    LOG.debug(result)
                    if ws:
                        # Send result to websocket (if using websockets)
                        return await ws.send_str(json.dumps(result))
                    else:
                        # Standard response
                        return result
                else:
                    # HTTP errors
                    if ws:
                        return await ws.send_str(json.dumps(str({"service": service,
                                                                 "queryParams": params,
                                                                 "responseStatus": response.status})))
                    else:
                        return {"service": service,
                                "queryParams": params,
                                "responseStatus": response.status}

        except Exception as e:
            LOG.debug(f'Query error {e}.')
            web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')
