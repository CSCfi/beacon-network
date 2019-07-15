"""Small General-Purpose Utility Functions."""

import os
import sys
import json
import ssl

import aiohttp

from aiohttp import web
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import JsonSerializer

from ..config import CONFIG
from .logging import LOG


async def http_get_service_urls(registry):
    """Query an external registry for known service urls of desired type."""
    LOG.debug('Query external registry for given service type.')
    service_urls = []

    # Query Registry for services
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(registry,
                                   ssl=await request_security()) as response:
                if response.status == 200:
                    result = await response.json()
                    for r in result:
                        # Check if service has a type tag of Beacons
                        if CONFIG.beacons and r.get('type') == 'urn:ga4gh:beacon':
                            service_urls.append(r['url'])
                        # Check if service has a type tag of Aggregators
                        if CONFIG.aggregators and r.get('type') == 'urn:ga4gh:aggregator':
                            service_urls.append(r['url'])
        except Exception as e:
            LOG.debug(f'Query error {e}.')
            web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')

    return service_urls


# Cache Beacon URLs if they're not already cached
@cached(ttl=86400, key="beacon_urls", serializer=JsonSerializer())
async def get_services(url_self):
    """Return service urls."""
    LOG.debug('Fetch service urls.')

    # Query Registries for their known Beacon services, fetch only URLs
    service_urls = set()
    for registry in CONFIG.registries:
        services = await http_get_service_urls(registry.get('url', ''))  # Request URLs from Registry
        service_urls.update(services)  # Add found URLs to set (eliminate duplicates)

    # Pre-process URLS
    service_urls = [await process_url(url) for url in service_urls]
    service_urls = await remove_self(url_self, service_urls)

    return service_urls


async def process_url(url):
    """Process URLs to the desired form.

    Some URLs might end with `/service-info`, others with `/` and some even `` (empty).
    The Aggregator wants to use the `/query` endpoint, so the URLs must be pre-processed for queries"""
    LOG.debug('Processing URLs.')

    if url.endswith('/'):
        url += 'query'
    elif url.endswith('/service-info'):
        url = url.replace('service-info', 'query')
    else:
        # Unknown case
        # One case is observed, where URL was similar to https://service.institution.org/beacon
        # For URLs where the info endpoint is /, but / is not present, let's add /query
        url += '/query'
        pass

    return url


async def remove_self(url_self, urls):
    """Remove self from list of service URLs to prevent infinite recursion.

    This use case is for when an Aggregator requests service URLs for Aggregators.
    The Aggregator should only query other Aggregators, not itself."""
    LOG.debug('Look for self from service URLs.')

    for url in urls:
        url_split = url.split('/')
        if url_self in url_split:
            urls.remove(url)
            LOG.debug('Found and removed self from service URLs.')

    return urls


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
    elif CONFIG.auth_cookie in request.cookies:
        LOG.debug('Session from cookies.')
        # Request access token from session storage
        access_token = await get_access_token_with_session()
    elif 'access_token' in request.cookies:
        LOG.debug('Auth from cookies.')
        # Then check if access token was stored in cookies
        access_token = request.cookies.get('access_token')
    else:
        LOG.debug('No auth.')
        # Otherwise send nothing
        # pass

    return access_token


async def get_access_token_with_session():
    """Request access token from session storage."""
    LOG.debug('Contacting session storage.')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(CONFIG.auth_url) as response:
                if response.status == 200:
                    LOG.debug(f'Session storage response: {response.status}.')
                    result = await response.json()
                    if 'access_token' in result:
                        LOG.debug('Access token received.')
                        return result.get('access_token', '')
                    else:
                        LOG.debug('Session storage did not contain an access token.')
                        return ''
        except Exception as e:
            LOG.debug(f'Query error {e}.')
            web.HTTPInternalServerError(text=f'An error occurred while attempting to query services: {e}')


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
            async with session.get(service,
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


async def validate_service_key(key):
    """Validate received service key."""
    LOG.debug('Validating service key.')

    for registry in CONFIG.registries:
        if key == registry.get('key'):
            # If a matching key is found, return true
            LOG.debug(f'Using service key of: {registry.get("url")}.')
            return True

    # If no matching keys were found, raise an exception
    raise web.HTTPUnauthorized(text='Unauthorized service key.')


async def clear_cache():
    """Clear cache of Beacons."""
    LOG.debug('Check if cache of Beacons exists.')

    try:
        cache = SimpleMemoryCache()
        if await cache.exists("beacon_urls"):
            LOG.debug('Found old cache.')
            await cache.delete("beacon_urls")
            LOG.debug('Cache has been cleared.')
        else:
            LOG.debug('No old cache found.')
        await cache.close()
    except Exception as e:
        LOG.error(f'Error at clearing cache: {e}.')


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
    LOG.debug('Check security level of application.')

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
@cached(ttl=86400, key="request_security")
async def request_security():
    """Determine requests' level of security.

    Security levels:
    Public
    0   Unsecure, server can be HTTP
    1   Secure, server must be HTTPS
    Private
    2   Server must be in the same closed trust network (possess same certs)

    Level of security is controlled with ENV `REQUEST_SECURITY` which takes int value 0-2."""
    LOG.debug('Check security level of request.')

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