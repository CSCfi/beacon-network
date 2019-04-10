"""Small General-Purpose Utility Functions."""

import os
import sys
import json
import secrets
import ssl

import aiohttp
import asyncio

from aiohttp import web
from aiocache import cached, SimpleMemoryCache
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
    allowed_params = ['serviceType', 'model', 'listFormat', 'apiVersion', 'remote']
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
            # raise web.HTTPNotFound(text=f'No queryable services found of service type {service_type}.')
            # Why did we even have a 404 here
            # pass
            # Return empty iterable
            return service_urls
    except Exception as e:
        LOG.debug(f'DB error for service_type={service_type}: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


# db function temporarily placed here due to import-loop issues
async def db_get_recaching_credentials(connection):
    """Return queryable service urls and service keys."""
    LOG.debug(f'Querying database for service urls and keys.')
    credentials = []
    try:
        # Database query
        query = f"""SELECT a.service_url AS service_url, b.service_key AS service_key
                    FROM services a, service_keys b
                    WHERE service_type='GA4GHBeaconAggregator'
                    AND a.id=b.service_id"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                credentials.append({'service_url': record['service_url'],
                                    'service_key': record['service_key']})
            return credentials
        else:
            # raise web.HTTPNotFound(text=f'No queryable services found of service type {service_type}.')
            # Why did we even have a 404 here
            # pass
            # Return empty iterable
            return credentials
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


async def clear_cache():
    """Clear cache of Beacons."""
    LOG.debug('Clear cached Beacons.')
    # Defines response status by HTTP standards
    # 201 if no cache pre-existed
    # 204 is an existing cache was overwritten
    response = 0

    try:
        cache = SimpleMemoryCache()
        if await cache.exists("beacon_urls"):
            LOG.debug('Found old cache.')
            response = 204
        else:
            LOG.debug('No old cache found.')
            response = 201
        await cache.delete("beacon_urls")
        await cache.close()
    except Exception as e:
        LOG.error(f'Error at clearing cache: {e}.')

    return response


async def cache_from_registry(beacons, response):
    """Cache Beacon URLs that were received from Registry's update message."""
    LOG.debug('Caching Beacons from Registry\'s update message.')

    try:
        cache = SimpleMemoryCache()
        await cache.set('beacon_urls', beacons)
        LOG.debug('Cache was set.')
    except Exception as e:
        response = 500
        LOG.error(f'Couldn\'t set cache: {e}.')

    return response


# Cache Beacon URLs if they're not already cached
@cached(ttl=86400, key="beacon_urls", serializer=JsonSerializer())
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
                # serviceUrl from DB: `https://../` append with `services`
                async with session.get(f'{service}services',
                                       params=params,
                                       ssl=await request_security()) as response:
                    if response.status == 200:
                        result = await response.json()
                        for r in result:
                            service_urls.append(r['serviceUrl'])
            except Exception as e:
                LOG.debug(f'Query error {e}.')
                web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')

    return service_urls


async def remote_recache_aggregators(request, db_pool):
    """Send a request to Aggregators to renew their Beacon caches."""
    LOG.debug('Starting remote re-caching of Aggregators.')

    tasks = []  # requests to be done
    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        aggregators = await db_get_recaching_credentials(connection)  # service urls (aggregators) to be queried, with service keys
        beacons = json.dumps(await db_get_service_urls(connection, service_type='GA4GHBeacon'))  # service urls (beacons) to be sent to aggregators

    for aggregator in aggregators:
        # Generate task queue
        task = asyncio.ensure_future(notify_service(aggregator, beacons))
        tasks.append(task)

    # Prepare and initiate co-routines
    await asyncio.gather(*tasks)


async def notify_service(service, beacons):
    """Contact given service and tell them to update their cache.

    Send list of up-to-date Beacon URLs to Aggregator."""
    LOG.debug('Notify service to update their cache.')

    # Send notification (request) to service (aggregator)
    async with aiohttp.ClientSession() as session:
        # try:
        # Solution for prototype, figure out a better way later
        # serviceUrl from DB: `https://../` append with `beacons`
        async with session.put(f'{service["service_url"]}beacons',
                               headers={'Beacon-Service-Key': service['service_key']},
                               data=beacons,
                               ssl=await request_security()) as response:
            if response.status in [200, 201, 204]:
                # 201 - cache didn't exist, and was created
                # 200/204 - cache existed, and was overwritten
                LOG.debug(f'Service received notification and responded with {response.status}.')
            else:
                LOG.debug('Service encountered a problem with notification.')
        # except Exception as e:
        #     LOG.debug(f'Query error {e}.')
        #     # web.HTTPInternalServerError(text=f'An error occurred while attempting to send request to Aggregator.')
        #     pass  # We don't care if a notification failed


async def query_service(service, params, access_token, ws=None):
    """Query service with params."""
    LOG.debug('Querying service.')
    headers = {}

    if access_token:
        headers.update({'Authorization': f'Bearer {access_token}'})

    # Query service in a session
    async with aiohttp.ClientSession() as session:
        try:
            # serviceUrl from DB: `https://../` append with `query`
            async with session.get(f'{service}query',
                                   params=params,
                                   headers=headers,
                                   ssl=await request_security()) as response:
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


async def http_verify_remote(remote):
    """Verify that provided address leads to a GA4GHRegistry."""
    LOG.debug('Verify that remote is a Registry.')
    # We don't need much information
    params = {'listFormat': 'short'}

    async with aiohttp.ClientSession() as session:
        try:
            # serviceUrl should be of form: `https://../` append with `info`
            async with session.get(f'{remote}info',
                                   params=params,
                                   ssl=await request_security()) as response:
                if response.status == 200:
                    result = await response.json()
                    if result['serviceType'] == 'GA4GHRegistry':
                        LOG.debug('Remote verified to be a Registry.')
                    else:
                        LOG.debug('Remote is not a Registry, or could not retrieve serviceType.')
                        raise web.HTTPBadRequest(text='Provided "remote" is not a GA4GHRegistry.')
                else:
                    LOG.debug('Provided "remote" was not found.')
                    raise web.HTTPNotFound(text='Provided "remote" not found.')
        except Exception as e:
            LOG.debug(f'Query error {e}.')
            raise web.HTTPInternalServerError(text=f'An error occurred while attempting to query remote: {e}')


async def http_register_at_remote(service, remote, remote_api_key):
    """Register at provided remote Registry."""
    LOG.debug('Register at remote.')
    headers = {'Post-Api-Key': remote_api_key}

    # Send POST request to remote Registry
    async with aiohttp.ClientSession() as session:
        # serviceUrl should be of form: `https://../` append with `services`
        async with session.post(f'{remote}services',
                                headers=headers,
                                data=json.dumps(service),
                                ssl=await request_security()) as response:
            if response.status in [200, 201, 202]:
                LOG.debug('Service was successfully registered at remote.')
                result = await response.json()
                return result['beaconServiceKey']
            else:
                message = await response.text()
                LOG.debug('Encountered problem with registration at remote.')
                # Terminate process here, forward the error
                if response.status == 400:
                    raise web.HTTPBadRequest(text=message)
                elif response.status == 401:
                    raise web.HTTPUnauthorized(text=message)
                elif response.status == 404:
                    raise web.HTTPNotFound(text=message)
                elif response.status == 409:
                    raise web.HTTPConflict(text=message)
                else:
                    # 500
                    raise web.HTTPInternalServerError(text=message)


# DB function temporarily in /utils due to import-loop issue
async def db_store_my_service_key(db_pool, remote_service, service_key):
    """Store my service key which is used at remote Registry."""
    LOG.debug('Store my remote service key.')

    # Take connection from database pool, re-use connection for all tasks
    async with db_pool.acquire() as connection:
        try:
            # Database commit occurs on transaction closure
            async with connection.transaction():
                await connection.execute("""INSERT INTO remote_keys (remote_service, service_key)
                                         VALUES ($1, $2)""",
                                         remote_service, service_key)
        except Exception as e:
            LOG.debug(f'DB error: {e}')
            raise web.HTTPInternalServerError(text='Database error occurred while attempting to store remote service key.')


async def remote_registration(db_pool, request, remote):
    """Forward registration request to a remote service."""
    LOG.debug('Remote registration.')
    # Get POST request body JSON as python dict
    service = await request.json()

    # Verify that remote is of type GA4GHRegistry
    await http_verify_remote(remote)
    # Register at remote, get the beaconServiceKey from response
    response = await http_register_at_remote(service, remote, request.headers['Remote-Api-Key'])
    # Store the service key from response for later use via PUT /beacons from Registry
    await db_store_my_service_key(db_pool, remote, response)

    return response


def load_certs(ssl_context):
    """Load certificates for SSLContext object."""
    LOG.debug('Load certificates for SSLContext.')

    try:
        ssl_context.load_cert_chain(os.environ.get('PATH_SSL_CERT_FILE', '/etc/ssl/certs/cert.pem'),
                                    keyfile=os.environ.get('PATH_SSL_KEY_FILE', '/etc/ssl/certs/key.pem'))
        ssl_context.load_verify_locations(cafile=os.environ.get('PATH_SSL_CA_FILE', '/etc/ssl/certs/ca.pem'))
    except Exception as e:
        LOG.error(f'Certificates not found {e}')
        sys.exit("""Could not find certificate files. Verify, that ENVs are set to point to correct .pem files!
                    export PATH_SSL_CERT_FILE=/location/of/certfile.pem
                    export PATH_SSL_KEY_FILE=/location/of/keyfile.pem
                    export PATH_SSL_CA_FILE=/location/of/cafile.pem""")

    return ssl_context


def application_security():
    """Determine application's level of security.

    Security levels:
    Public
    0   App HTTP
    1   App HTTPS
    Private
    2   Closed network node (cert sharing)

    Level of security is controlled with ENV `APPLICATION_SECURITY` which takes int value 0-2."""
    LOG.debug('Check application level of security.')

    # Convert ENV string to int
    level = int(os.environ.get('APPLICATION_SECURITY', 0))

    ssl_context = None

    if level == 0:
        LOG.debug(f'Application security level {level}.')
    elif level == 1:
        LOG.debug(f'Application security level {level}.')
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context = load_certs(ssl_context)
    elif level == 2:
        LOG.debug(f'Application security level {level}.')
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context = load_certs(ssl_context)
    else:
        LOG.debug(f'Could not determine application security level ({level}), setting to default (0).')

    return ssl_context


# We expect this to be used frequently
@cached(ttl=86400, key="request_security", serializer=JsonSerializer())
async def request_security():
    """Determine requests' level of security.

    Security levels:
    Public
    0   Unsecure, server can be HTTP
    1   Secure, server must be HTTPS
    Private
    2   Server must be in the same closed trust network (possess same certs)

    Level of security is controlled with ENV `REQUEST_SECURITY` which takes int value 0-2."""
    LOG.debug('Check request level of security.')

    # Convert ENV string to int
    level = int(os.environ.get('REQUEST_SECURITY', 0))

    ssl_context = False

    if level == 0:
        LOG.debug(f'Request security level {level}.')
    elif level == 1:
        LOG.debug(f'Request security level {level}.')
        ssl_context = True
    elif level == 2:
        LOG.debug(f'Request security level {level}.')
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context = load_certs(ssl_context)
    else:
        LOG.debug(f'Could not determine request security level ({level}), setting to default (0).')

    return ssl_context
