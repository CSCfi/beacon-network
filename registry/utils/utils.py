"""Small General-Purpose Utility Functions."""

import os
import sys
import secrets
import ssl
import re

import aiohttp
import asyncio

from aiohttp import web
from aiocache import cached

from .logging import LOG
from ..config import CONFIG


async def http_request_info(url):
    """Request service info of given URL."""
    LOG.debug("Send a request to given URL to get service info.")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, ssl=await request_security()) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    LOG.debug(f"{url} not found.")
                    raise web.HTTPNotFound(text=f"{url} not found.")
        except Exception as e:
            LOG.debug(f"Query error {e}.")
            raise web.HTTPInternalServerError(text=f"An error occurred while attempting to contact service: {e}")


async def parse_service_info(id, service, req={}):
    """Parse and validate service info.

    Service infos may use the same keys in different places, for example the
    Beacon API specification differs slightly from GA4GH service-info specification.
    This issue should be fixed in a future product-approval-process (PAP) of Beacon API.
    """
    LOG.debug("Parsing service info.")

    service_info = {}

    if req.get("url", "").endswith("/service-info"):
        LOG.debug("Using GA4GH endpoint.")
        # Use GA4GH service-info notation
        service_info = {
            "id": id,
            "name": service.get("name", ""),
            "type": service.get("type", {}).get("artifact"),
            "description": service.get("description", ""),
            "url": req.get("url", "") or service.get("url", ""),
            "contact_url": service.get("contactUrl", ""),
            "api_version": service.get("type", {}).get("version"),
            "service_version": service.get("version", ""),
            "environment": service.get("environment", ""),
            "organization": service.get("organization").get("name"),
            "organization_url": service.get("organization").get("url", ""),
            "organization_logo": service.get("organization").get("logoUrl", ""),
        }
    else:
        LOG.debug("Using Beacon API endpoint.")
        # Use Beacon API spec notation
        # Beacon API `/` doesn't have `type` or `environment`, so it's set here by default
        # If `apiVersion` is missing, we expect at least >1.0.0
        service_info = {
            "id": id,
            "name": service.get("name", ""),
            "type": "beacon",
            "description": service.get("description", ""),
            "url": req.get("url", "") or service.get("url", ""),
            "contact_url": service.get("organization", {}).get("contactUrl", ""),
            "api_version": service.get("apiVersion", "1.0.0"),
            "service_version": service.get("version", ""),
            "environment": service.get("environment", "prod"),
            "organization": service.get("organization").get("name"),
            "organization_url": service.get("organization").get("welcomeUrl", ""),
            "organization_logo": service.get("organization").get("logoUrl", ""),
        }

    # Validate service info, raise a fatal exception on any issue
    if CONFIG.test is False:
        await validate_service_info(service_info, service.get("id"))

    return service_info


async def validate_service_info(service, fetched_service_id):
    """Validate parsed service info object."""
    LOG.debug("Validating parsed service info.")
    regex = r"[^@]+@[^@]+\.[^@]+"  # simple email validator
    # `service` has been pre-parsed, it contains the correct form of id in `service['id]`
    # `fetched_service_if` is the id given by the service in their info object

    # The registry will validate that all URLs begin with `https://` if they are set,
    # because all traffic in the Beacon Network UI must be encrypted.
    # The id will also be validated that it follows Beacon API specification convention:
    # The id should be equal to "reverse domain name", so that it can be seamlessly utilised
    # In the UI to display more information about query responses using the Registry/services/<service-id> endpoint
    if service["id"] != fetched_service_id:
        raise web.HTTPBadRequest(
            text=f'Service ID that was fetched from info endpoint was rejected. Received "{fetched_service_id}", '
            + f'when expected "{service["id"]}". Service ID must follow reverse domain name notation '
            + "according to Beacon API specification."
        )

    if not service["url"].startswith("https://"):
        raise web.HTTPBadRequest(text=f'Service URL was rejected. Received "{service["url"]}". Service URL must begin with https://.')
    if service["contact_url"] != "" and not service["contact_url"].startswith(("https://", "mailto:")) and not re.search(regex, service["contact_url"]):
        raise web.HTTPBadRequest(
            text=f'Contact URL was rejected. Received "{service["contact_url"]}". Contact URL must begin with https:// or mailto: '
            "or be a valid email address."
        )
    if service["organization_url"] != "" and not service["organization_url"].startswith("https://"):
        raise web.HTTPBadRequest(text=f'Organization URL was rejected. Received "{service["organization_url"]}". Organization URL must begin with https://.')
    if service["organization_logo"] != "" and not service["organization_logo"].startswith("https://"):
        raise web.HTTPBadRequest(text=f'Logo URL was rejected. Received "{service["organization_logo"]}". Logo URL must begin with https://.')


async def construct_json(data):
    """Construct proper JSON response from dictionary data."""
    LOG.debug("Construct JSON response from DB record.")
    # With the final GA4GH service info 1.0.0 release type str was changed to type object
    # we will keep the database unchanged, and assume that group is always org.ga4gh
    # type will represent type artifact and api_version will represent type version
    response = {
        "id": data.get("id", ""),
        "name": data.get("name", ""),
        "type": {"group": "org.ga4gh", "artifact": data.get("type", ""), "version": data.get("api_version", "")},
        "description": data.get("description", ""),
        "organization": {"name": data.get("organization", ""), "url": data.get("organization_url", ""), "logoUrl": data.get("organization_logo", "")},
        "contactUrl": data.get("contact_url", ""),
        "createdAt": str(data.get("created_at", "")),
        "updatedAt": str(data.get("updated_at", "")),
        "environment": data.get("environment", ""),
        "version": data.get("service_version", ""),
        "url": data.get("url", ""),
    }
    return response


async def query_params(request):
    """Parse query string params from path."""
    LOG.debug("Parse query params.")
    # Query string params
    params = {"type": request.query.get("type", None), "apiVersion": request.query.get("apiVersion", None)}
    # Path param
    service_id = request.match_info.get("service_id", None)
    return service_id, params


# db function temporarily placed here due to import-loop issues
async def db_get_service_urls(connection, service_type=None):
    """Return queryable service urls."""
    LOG.debug(f"Querying database for service urls of type {service_type}.")
    service_urls = []
    try:
        # Database query
        query = """SELECT service_url FROM services WHERE service_type=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(service_type)
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                service_urls.append(record["service_url"])
            return service_urls
        else:
            # raise web.HTTPNotFound(text=f'No queryable services found of service type {service_type}.')
            # Why did we even have a 404 here
            # pass
            # Return empty iterable
            return service_urls
    except Exception as e:
        LOG.debug(f"DB error for service_type={service_type}: {e}")
        raise web.HTTPInternalServerError(text="Database error occurred while attempting to fetch service urls.")


# db function temporarily placed here due to import-loop issues
async def db_get_recaching_credentials(connection):
    """Return queryable service urls and service keys."""
    LOG.debug("Querying database for service urls and keys.")
    credentials = []
    try:
        # Database query
        query = """SELECT a.url AS url, b.service_key AS service_key
                   FROM services a, service_keys b
                   WHERE type='aggregator'
                   AND a.id=b.service_id"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                credentials.append({"service_url": record["url"], "service_key": record["service_key"]})
            return credentials
        else:
            return credentials
    except Exception as e:
        LOG.debug(f"DB error: {e}")
        raise web.HTTPInternalServerError(text="Database error occurred while attempting to fetch service urls.")


async def invalidate_aggregator_caches(request, db_pool):
    """Invalidate caches at Aggregators."""
    LOG.debug("Invalidate cached Beacons at Aggregators.")

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
    LOG.debug("Notify service to delete their cache.")

    # Send invalidation notification (request) to service (aggregator)
    async with aiohttp.ClientSession() as session:
        try:
            # Aggregator URLs end with /service-info in the DB, replace them with /cache
            async with session.delete(
                service["service_url"].replace("service-info", "cache"), headers={"Authorization": service["service_key"]}, ssl=await request_security()
            ) as response:
                if response.status in [200, 204]:
                    LOG.debug(f"Service received notification and responded with {response.status}.")
                else:
                    # Low priority log, it doesn't matter if the invalidation was unsuccessful
                    LOG.debug(f"Service encountered a problem with notification: {response.status}.")
        except Exception as e:
            LOG.debug(f"Query error {e}.")
            # web.HTTPInternalServerError(text=f'An error occurred while attempting to send request to Aggregator.')
            pass  # We don't care if a notification failed


async def generate_service_key():
    """Generate a service key."""
    LOG.debug("Generate service key.")
    return secrets.token_urlsafe(64)


async def generate_service_id(url):
    """Generate service ID from given URL."""
    LOG.debug("Generate service ID.")
    address = url.split("://")  # strip http schema if it exists
    domain = (0, 1)[len(address) > 1]  # index of domain in schemaless address
    domain = address[domain].split("/")  # distinguish endpoints
    service_id = ".".join(reversed(domain[0].split(".")))  # reverse domain to create id
    return service_id


def load_certs(ssl_context):
    """Load certificates for SSLContext object."""
    LOG.debug("Load certificates for SSLContext.")

    try:
        ssl_context.load_cert_chain(
            os.environ.get("PATH_SSL_CERT_FILE", "/etc/ssl/certs/cert.pem"), keyfile=os.environ.get("PATH_SSL_KEY_FILE", "/etc/ssl/certs/key.pem")
        )
        ssl_context.load_verify_locations(cafile=os.environ.get("PATH_SSL_CA_FILE", "/etc/ssl/certs/ca.pem"))
    except Exception as e:
        LOG.error(f"Certificates not found {e}")
        sys.exit(
            """Could not find certificate files. Verify, that ENVs are set to point to correct .pem files!
                    export PATH_SSL_CERT_FILE=/location/of/certfile.pem
                    export PATH_SSL_KEY_FILE=/location/of/keyfile.pem
                    export PATH_SSL_CA_FILE=/location/of/cafile.pem"""
        )

    return ssl_context


def application_security():
    """Determine application's level of security.

    Security levels:
    Public
    0   App HTTP
    1   App HTTPS
    Private
    2   Closed network node (cert sharing)

    Level of security is controlled with ENV `APPLICATION_SECURITY` which takes int value 0-2.
    """
    LOG.debug("Check security level of application.")

    # Convert ENV string to int
    level = int(os.environ.get("APPLICATION_SECURITY", 0))

    ssl_context = None

    if level == 0:
        LOG.debug(f"Application security level {level}.")
    elif level == 1:
        LOG.debug(f"Application security level {level}.")
        ssl_context = ssl.create_default_context()
        ssl_context = load_certs(ssl_context)
    elif level == 2:
        LOG.debug(f"Application security level {level}.")
        # This means, that clients that connect to this Registry (server)
        # are required to authenticate (they must have the correct cert)
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context = load_certs(ssl_context)
    else:
        LOG.debug(f"Could not determine application security level ({level}), setting to default (0).")

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

    Level of security is controlled with ENV `REQUEST_SECURITY` which takes int value 0-2.
    """
    LOG.debug("Check security level of request.")

    # Convert ENV string to int
    level = int(os.environ.get("REQUEST_SECURITY", 0))

    ssl_context = False

    if level == 0:
        LOG.debug(f"Request security level {level}.")
    elif level == 1:
        LOG.debug(f"Request security level {level}.")
        ssl_context = True
    elif level == 2:
        LOG.debug(f"Request security level {level}.")
        # Servers that this app requests (as a client) must have the correct certs
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context = load_certs(ssl_context)
    else:
        LOG.debug(f"Could not determine request security level ({level}), setting to default (0).")

    return ssl_context
