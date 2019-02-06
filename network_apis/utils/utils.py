"""Small General-Purpose Utility Functions."""

import os
import json
import secrets

import aiohttp

from aiohttp import web

from .logging import LOG
# from .db_ops import db_get_service_urls


async def construct_json(data, model=None, list_format='full'):
    """Construct proper JSON response from dictionary data."""
    LOG.debug('Construct JSON response from DB record.')
    # Minimal body when list_format='short'
    response = {
        "id": data.get('ser_id', ''),
        "name": data.get('ser_name', ''),
        "serviceType": data.get('ser_service_type', ''),
        "serviceUrl": data.get('ser_service_url', ''),
        "open": data.get('ser_open', '')
    }

    if list_format == 'full':
        # if list_format='full' or not specified -> defaults to full
        # update response to include all keys
        response.update(
            {
                "apiVersion": data.get('ser_api_version', ''),
                "organization": {
                    "id": data.get('org_id', ''),
                    "name": data.get('org_name', ''),
                    "description": data.get('org_description', ''),
                    "address": data.get('org_address', ''),
                    "welcomeUrl": data.get('org_welcome_url', ''),
                    "contactUrl": data.get('org_contact_url', ''),
                    "logoUrl": data.get('org_logo_url', ''),
                    "info": {}
                },
                "description": data.get('ser_description', ''),
                "version": data.get('ser_service_version', ''),
                "publicKey": data.get('ser_public_key', ''),
                "welcomeUrl": data.get('ser_welcome_url', ''),
                "alternativeUrl": data.get('ser_alt_url', ''),
                "createDateTime": str(data.get('ser_createtime', '')),
                "updateDateTime": str(data.get('ser_updatetime', ''))
            }
        )
        if 'org_info' in data:
            # Load the jsonb string into a dict and update the info-key
            response['organization']['info'].update(json.loads(data.get('org_info', '')))

    return response


async def query_params(request):
    """Parse query string params from path."""
    LOG.debug('Parse query params.')
    # Query string params
    allowed_params = ['serviceType', 'model', 'listFormat', 'apiVersion']
    params = {k: v for k, v in request.rel_url.query.items() if k in allowed_params}
    # Path param
    service_id = request.match_info.get('service_id', None)
    return service_id, params


async def fetch_service_key(request):
    """Fetch service key from headers."""
    LOG.debug('Fetch service key.')
    return request.headers.get('Beacon-Service-Key')


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


# db function temporarily placed here due to import-loop issues
async def db_get_service_urls(connection):
    """Return queryable service urls."""
    LOG.debug('Querying database for service urls.')
    service_urls = []
    try:
        # Database query
        # Limit search to Beacons for now, add <OR service_type='GA4GHBeaconAggregator'> later if necessary
        query = f"""SELECT service_url FROM services WHERE service_type='GA4GHBeacon'"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                service_urls.append(record['service_url'])
            return service_urls
        else:
            raise web.HTTPNotFound(text='No queryable services found.')
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


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
                # On successful response, forward response
                if response.status == 200:
                    result = await response.json()
                    if isinstance(ws, web.WebSocketResponse):
                        # Send result to websocket (if using websockets)
                        return await ws.send_str(json.dumps(result))
                    else:
                        # Standard response
                        return result
                else:
                    # HTTP errors
                    error = {"service": service,
                             "queryParams": params,
                             "responseStatus": response.status}
                    if ws:
                        return await ws.send_str(json.dumps(str(error)))
                    else:
                        return error

        except Exception as e:
            LOG.debug(f'Query error {e}.')
            web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')


async def generate_service_key():
    """Generate a service key."""
    LOG.debug('Generate service key.')
    return secrets.token_urlsafe(64)
