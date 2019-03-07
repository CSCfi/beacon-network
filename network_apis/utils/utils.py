"""Small General-Purpose Utility Functions."""

import os
import json
import secrets

from distutils.util import strtobool

import aiohttp

from aiohttp import web
from aiocache import cached
from aiocache.serializers import JsonSerializer

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
        # pass

    return access_token


# db function temporarily placed here due to import-loop issues
async def db_get_service_urls(connection, service_type=None):
    """Return queryable service urls."""
    LOG.debug(f'Querying database for service urls of type {service_type}.')
    service_urls = []
    try:
        # Database query
        query = f"""SELECT service_url FROM services WHERE service_type=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(service_type)
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                service_urls.append(record['service_url'])
            return service_urls
        else:
            raise web.HTTPNotFound(text=f'No queryable services found of service type {service_type}.')
    except Exception as e:
        LOG.debug(f'DB error for service_type={service_type}: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


# Cache Beacon URLs for faster re-usability
@cached(ttl=604800, key="beacon_urls", serializer=JsonSerializer())
async def get_services(db_pool):
    """Return service urls."""
    LOG.debug('Fetch service urls.')

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        services = await db_get_service_urls(connection, service_type='GA4GHRegistry')  # service urls (in this case registries) to be queried

    # Query Registries for their known Beacon services, fetch only URLs
    service_urls = await http_get_service_urls(services, service_type='GA4GHBeacon')

    return service_urls


async def http_get_service_urls(services, service_type=None):
    """Query a an external service for known service urls."""
    LOG.debug('Query external service for given service type.')
    service_urls = []
    # Here we want to find Beacons (can be re-used for other purposes too) and in short format for smaller payload
    params = {'serviceType': service_type, 'listFormat': 'short'}

    # Query service (typically a registry) in a session
    async with aiohttp.ClientSession() as session:
        for service in services:
            try:
                async with session.get(service,
                                       params=params,
                                       ssl=bool(strtobool(os.environ.get('HTTPS_ONLY', 'False')))) as response:
                    if response.status == 200:
                        result = await response.json()
                        for r in result:
                            service_urls.append(r['serviceUrl'])
            except Exception as e:
                LOG.debug(f'Query error {e}.')
                web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')

    return service_urls


async def query_service(service, params, access_token, ws=None):
    """Query service with params."""
    LOG.debug('Querying service.')
    headers = {}

    if access_token:
        headers.update({'Authorization': f'Bearer {access_token}'})

    # Query service in a session
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(service,
                                   params=params,
                                   ssl=bool(strtobool(os.environ.get('HTTPS_ONLY', 'False'))),
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


# This is currently not used, but is kept for possible future implementation
# The idea is, that the user doesn't give the id, but it is generated from the
# Given service url, so that the id is always unique as it is tied to the registered url
# def generate_service_id(url):
#     """Generate service ID from given URL."""
#     LOG.debug('Generate service ID.')
#     address = url.split('://')  # strip http schema if it exists
#     domain = (0,1)[len(address)>1]  # index of domain in schemaless address
#     domain = address[domain].split('/')  # distinguish endpoints
#     service_id = '.'.join(reversed(domain[0].split('.')))  # reverse domain to create id
#     return service_id
