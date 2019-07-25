"""Small General-Purpose Utility Functions."""

import os
import sys
import json
import secrets
import ssl

import aiohttp
import asyncio

from aiohttp import web
from aiocache import cached

from .logging import LOG


async def http_request_info(url):
    """Request service info of given URL."""
    LOG.debug('Send a request to given URL to get service info.')

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url,
                                   ssl=await request_security()) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    LOG.debug(f'{url} not found.')
                    raise web.HTTPNotFound(text=f'{url} not found.')
        except Exception as e:
            LOG.debug(f'Query error {e}.')
            raise web.HTTPInternalServerError(text=f'An error occurred while attempting to contact service: {e}')


async def parse_service_info(id, service, req={}):
    """Parse and validate service info.

    Service infos may use the same keys in different places, for example the
    Beacon API specification differs slightly from GA4GH service-info specification.
    This issue should be fixed in a future product-approval-process (PAP) of Beacon API."""
    LOG.debug('Parsing service info.')

    service_info = {}

    if req.get('url', '').endswith('/service-info'):
        LOG.debug('Using GA4GH endpoint.')
        # Use GA4GH service-info notation
        service_info = {
            'id': id,
            'name': service.get('name', ''),
            'type': service.get('type', 'urn:ga4gh:beacon'),
            'description': service.get('description', ''),
            'url': req.get('url', '') or service.get('url', ''),
            'contact_url': service.get('contactUrl', ''),
            'api_version': service.get('apiVersion', ''),
            'service_version': service.get('version', ''),
            'extension': service.get('extension', {})
        }
    else:
        LOG.debug('Using Beacon API endpoint.')
        # Use Beacon API spec notation
        service_info = {
            'id': id,
            'name': service.get('name', ''),
            'type': 'urn:ga4gh:beacon',
            'description': service.get('description', ''),
            'url': req.get('url', '') or service.get('url', ''),
            'contact_url': service.get('organization', {}).get('contactUrl', ''),
            'api_version': service.get('apiVersion', ''),
            'service_version': service.get('version', ''),
            'extension': service.get('info', {})
        }
        try:
            # add following Beacon API keys to extension for UI use
            # organization.name
            # organization.welcomeUrl
            # organization.logoUrl
            service_info['extension'].update(
                {
                    'organization': {
                        'name': service.get('organization').get('name'),
                        'welcomeUrl': service.get('organization').get('welcomeUrl'),
                        'logoUrl': service.get('organization').get('logoUrl')
                    }
                }
            )
        except Exception as e:
            LOG.debug(f'Failed to update extension: {e}.')
            pass

    return service_info


async def construct_json(data):
    """Construct proper JSON response from dictionary data."""
    LOG.debug('Construct JSON response from DB record.')
    response = {
        'id': data.get('id', ''),
        'name': data.get('name', ''),
        'type': data.get('type', ''),
        'description': data.get('description', ''),
        'url': data.get('url', ''),
        'createdAt': str(data.get('created_at', '')),
        'updatedAt': str(data.get('updated_at', '')),
        'contactUrl': data.get('contact_url', ''),
        'apiVersion': data.get('api_version', ''),
        'version': data.get('service_version', ''),
        'extension': json.loads(data.get('extension', {}))
    }
    return response


async def query_params(request):
    """Parse query string params from path."""
    LOG.debug('Parse query params.')
    # Query string params
    allowed_params = ['type', 'apiVersion']
    params = {k: v for k, v in request.rel_url.query.items() if k in allowed_params}
    # Path param
    service_id = request.match_info.get('service_id', None)
    return service_id, params


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
        query = f"""SELECT a.url AS url, b.service_key AS service_key
                    FROM services a, service_keys b
                    WHERE type='urn:ga4gh:aggregator'
                    AND a.id=b.service_id"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                credentials.append({'service_url': record['url'],
                                    'service_key': record['service_key']})
            return credentials
        else:
            return credentials
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


async def invalidate_aggregator_caches(request, db_pool):
    """Invalidate caches at Aggregators."""
    LOG.debug('Invalidate cached Beacons at Aggregators.')

    tasks = []  # requests to be done
    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        aggregators = await db_get_recaching_credentials(connection)  # service urls (aggregators) to be queried, with service keys

    for aggregator in aggregators:
        # Generate task queue
        task = asyncio.ensure_future(invalidate_cache(aggregator))
        tasks.append(task)

    # Prepare and initiate co-routines
    await asyncio.gather(*tasks)


async def invalidate_cache(service):
    """Contact given service and tell them to delete their cache."""
    LOG.debug('Notify service to delete their cache.')

    # Send invalidation notification (request) to service (aggregator)
    async with aiohttp.ClientSession() as session:
        try:
            # Aggregator URLs end with /service-info in the DB, replace them with /cache
            async with session.delete(service["service_url"].replace('service-info', 'cache'),
                                      headers={'Beacon-Service-Key': service['service_key']},
                                      ssl=await request_security()) as response:
                if response.status in [200, 204]:
                    LOG.debug(f'Service received notification and responded with {response.status}.')
                else:
                    # Low priority log, it doesn't matter if the invalidation was unsuccessful
                    LOG.debug(f'Service encountered a problem with notification: {response.status}.')
        except Exception as e:
            LOG.debug(f'Query error {e}.')
            # web.HTTPInternalServerError(text=f'An error occurred while attempting to send request to Aggregator.')
            pass  # We don't care if a notification failed


async def generate_service_key():
    """Generate a service key."""
    LOG.debug('Generate service key.')
    return secrets.token_urlsafe(64)


async def generate_service_id(url):
    """Generate service ID from given URL."""
    LOG.debug('Generate service ID.')
    address = url.split('://')  # strip http schema if it exists
    domain = (0, 1)[len(address) > 1]  # index of domain in schemaless address
    domain = address[domain].split('/')  # distinguish endpoints
    service_id = '.'.join(reversed(domain[0].split('.')))  # reverse domain to create id
    return service_id


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
