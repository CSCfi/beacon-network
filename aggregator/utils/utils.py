"""Small General-Purpose Utility Functions."""
import json
import os
import sys
from typing import List, Any

import ujson
import ssl

from urllib import parse

import aiohttp
import asyncio
import uvloop

from aiohttp import web
from aiocache import cached, SimpleMemoryCache
from aiocache.serializers import JsonSerializer
from aiohttp_session import get_session

from ..config import CONFIG
from .logging import LOG
from ..constants import SESSION_KEY_CILOGON_TOKEN
from ..endpoints.query import BeaconEndpoint

# Used by query_service() and ws_bundle_return() in a similar manner as ../endpoints/query.py
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def parse_version(semver):
    """
    Parse the major version from a string semver.

    This is required, because some services use `2.0.0` and some `v2.0.0`
    """
    LOG.debug("Parsing version number.")

    # if the service is missing a version number, we expect it to be Beacon 1.0
    if semver == "":
        return 1

    # parse the major version out of semver string and ignore any strings if they are present
    # e.g.
    # 1.0.0 -> 1
    # v2.0.0 -> 2
    if (version := "".join(filter(str.isdigit, semver.split(".")[0]))) != "":
        return int(version)


async def http_get_service_urls(registry):
    """Query an external registry for known service urls of desired type."""
    LOG.debug("Query external registry for given service type.")
    service_urls = []

    # Query Registry for services
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(registry, ssl=await request_security()) as response:
                if response.status == 200:
                    result = await response.json()
                    for r in result:
                        # Parse types: query beacons, or query aggregators, or both?
                        # Check if service has a type tag of Beacons
                        if (
                            CONFIG.beacons
                            and r.get("type", {}).get("artifact") == "beacon"
                        ):
                            # Create a tuple of URL and service version
                            # the version is used later in deciding the request body
                            service_urls.append(
                                (
                                    r["url"],
                                    await parse_version(r.get("type").get("version")),
                                    "beacon",
                                )
                            )
                        # Check if service has a type tag of Aggregators
                        if (
                            CONFIG.aggregators
                            and r.get("type", {}).get("artifact") == "beacon-aggregator"
                        ):
                            service_urls.append(
                                (
                                    r["url"],
                                    await parse_version(r.get("type").get("version")),
                                    "beacon-aggregator",
                                )
                            )
        except Exception as e:
            LOG.debug(f"Query error {e}.")
            web.HTTPInternalServerError(
                text="An error occurred while attempting to query services."
            )

    return service_urls


# Cache Beacon URLs if they're not already cached
@cached(ttl=86400, key="beacon_urls", serializer=JsonSerializer())
async def get_services(url_self):
    """Return service urls."""
    LOG.debug("Fetch service urls.")

    # Query Registries for their known Beacon services, fetch only URLs
    service_urls = set()
    for registry in CONFIG.registries:
        services = await http_get_service_urls(
            registry.get("url", "")
        )  # Request URLs from Registry
        service_urls.update(services)  # Add found URLs to set (eliminate duplicates)

    # Pre-process URLS
    service_urls = [await process_url(url) for url in service_urls]
    service_urls = await remove_self(url_self, service_urls)

    return service_urls


async def process_url(url):
    """Process URLs to the desired form.

    Some URLs might end with `/service-info`, others with `/` and some even `` (empty).
    The Aggregator wants to use the `/query` endpoint, so the URLs must be pre-processed for queries.
    New in Beacon 2.0: `/g_variants` endpoint replaces the 1.0 `/query` endpoint.
    """
    LOG.debug("Processing URLs.")
    # convert tuple to list for processing
    url = list(url)
    # Check which endpoint to use, Beacon 1.0 or 2.0
    query_endpoints = ["query"]
    if url[1] == 2:
        query_endpoints = [
            "individuals",
            "g_variants",
            "biosamples",
            "runs",
            "analyses",
            "interactors",
            "cohorts",
            "filtering_terms",
        ]

    LOG.debug(f"Using endpoint {query_endpoints}")
    urls = []
    # Add endpoint
    if url[0].endswith("/"):
        for endpoint in query_endpoints:
            urls.append([url[0] + endpoint, url[1]])
    elif url[0].endswith("/service-info"):
        for endpoint in query_endpoints:
            urls.append([url[0].replace("service-info", endpoint), url[1]])
    else:
        # Unknown case
        # One case is observed, where URL was similar to https://service.institution.org/beacon
        # For URLs where the info endpoint is /, but / is not present, let's add /query
        for endpoint in query_endpoints:
            urls.append([url[0] + "/" + endpoint, url[1]])

        pass

    # convert back to tuple after processing
    urlTuples = []
    for url in urls:
        urlTuples.append(tuple(url))
    return urlTuples


async def remove_self(url_self, urls):
    """Remove self from list of service URLs to prevent infinite recursion.

    This use case is for when an Aggregator requests service URLs for Aggregators.
    The Aggregator should only query other Aggregators, not itself.
    """
    LOG.debug("Look for self from service URLs.")

    for url in urls:
        url = list(url)
        for u in url[0]:
            url_split = str(u).split("/")
            if url_self in url_split:
                urls.remove(url)
                LOG.debug("Found and removed self from service URLs.")

    return urls


async def get_access_token(request):
    """Retrieve access token if it exists."""
    LOG.debug("Look for access token.")
    access_token = None

    session = await get_session(request)

    if "Authorization" in request.headers:
        LOG.debug("Auth from headers.")
        try:
            # First check if access token was delivered via headers
            auth_scheme, access_token = request.headers.get("Authorization").split(" ")
            if not auth_scheme == "Bearer":
                LOG.debug(f'User tried to use "{auth_scheme}"" auth_scheme.')
                raise web.HTTPBadRequest(
                    text=f'Unallowed authorization scheme "{auth_scheme}", user "Bearer" instead.'
                )
        except ValueError as e:
            LOG.debug(f"Error while attempting to get token from headers: {e}")
            raise web.HTTPBadRequest(
                text='Authorization header requires "Bearer" scheme.'
            )
    elif "access_token" in request.cookies:
        LOG.debug("Auth from cookies.")
        # Then check if access token was stored in cookies
        access_token = request.cookies.get("access_token")
    elif SESSION_KEY_CILOGON_TOKEN in session:
        access_token = session[SESSION_KEY_CILOGON_TOKEN]
    else:
        LOG.debug("No auth.")
        # Otherwise send nothing
        # pass

    return access_token


async def pre_process_payload(version, params):
    """
    Pre-process GET query string into POST payload.

    This function serves as a translator between Beacon 1.0 and 2.0 specifications.
    """
    LOG.debug(f"Processing payload for version {str(version)}.")

    # parse the query string into a dict
    raw_data = dict(parse.parse_qsl(params))
    if version == 2:
        # checks if a query is a listing search
        if (raw_data.get("referenceName")) is not None:
            data = pre_process_beacon2(raw_data)
        else:
            # beaconV2 expects some data but in listing search these are not needed and therefore they are empty
            data = {"assemblyId": "", "includeDatasetResponses": ""}
            if (filter := raw_data.get("filters")) != "None" and (
                raw_data.get("filters")
            ) != "null":
                data["filters"] = filter
        return data
    else:
        # convert string digits into integers
        # Beacon 1.0 uses integer coordinates, while Beacon 2.0 uses string coordinates (ignore referenceName, it should stay as a string)
        raw_data = {
            k: int(v) if v.isdigit() and k != "referenceName" else v
            for k, v in raw_data.items()
        }
        # Beacon 1.0
        # Unmodified structure for version 1, straight parsing from GET query string to POST payload
        data = raw_data
        # datasetIds must be a list instead of a string
        if "datasetIds" in data:
            data["datasetIds"] = data["datasetIds"].split(",")
    return data


def pre_process_beacon2(raw_data):
    """Pre-process GET query string into POST payload for beacon2."""
    # default data which is always present
    data = {
        "assemblyId": raw_data.get("assemblyId"),
        "includeDatasetResponses": raw_data.get("includeDatasetResponses"),
    }
    # optionals
    if (rn := raw_data.get("referenceName")) is not None:
        data["referenceName"] = rn
    if (vt := raw_data.get("variantType")) is not None:
        data["variantType"] = vt
    if (rb := raw_data.get("referenceBases")) is not None:
        data["referenceBases"] = rb
    if (ab := raw_data.get("alternateBases")) is not None:
        data["alternateBases"] = ab
    if (di := raw_data.get("datasetIds")) is not None:
        data["datasetIds"] = di.split(",")
    # exact coordinates
    if (s := raw_data.get("start")) is not None:
        data["start"] = s
    if (e := raw_data.get("end")) is not None:
        data["end"] = e
    # range coordinates
    if (smin := raw_data.get("startMin")) is not None and (
        smax := raw_data.get("startMax")
    ) is not None:
        data["start"] = ",".join([smin, smax])
    if (emin := raw_data.get("endMin")) is not None and (
        emax := raw_data.get("endMax")
    ) is not None:
        data["end"] = ",".join([emin, emax])
    if (filter := raw_data.get("filters")) is not None:
        data["filters"] = filter
    return data


async def pre_process_post_payload(version, params, filter_options):
    """
    Pre-process GET query string into POST payload.
    This function serves as a translator between Beacon 1.0 and 2.0 specifications.
    """
    LOG.debug(f"Processing post payload for version {str(version)}.")
    # parse the query string into a dict
    raw_data = dict(parse.parse_qsl(params))
    if version == 2:
        # checks if a query is a listing search
        if (filter_options) is not None:
            data = filter_options

        elif (raw_data.get("referenceName")) is not None:
            data = pre_process_beacon2(raw_data)
        else:
            # beaconV2 expects some data but in listing search these are not needed thus they are empty
            data = {"assemblyId": "", "includeDatasetResponses": ""}

    else:
        # convert string digits into integers
        # Beacon 1.0 uses integer coordinates, while Beacon 2.0 uses string coordinates (ignore referenceName, it should stay as a string)
        raw_data = {
            k: int(v) if v.isdigit() and k != "referenceName" else v
            for k, v in raw_data.items()
        }
        # Beacon 1.0
        # Unmodified structure for version 1, straight parsing from GET query string to POST payload
        data = raw_data
    return data


async def post_query_service(endpoint: BeaconEndpoint, access_token: str, body: Any):
    """Query service with params."""
    LOG.debug("post_query_service")

    headers = {}

    if access_token:
        headers.update({"Authorization": f"Bearer {access_token}"})

    # Query service in a session
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                endpoint["individuals"],
                json=body,
                headers=headers,
                ssl=await request_security(),
            ) as response:
                LOG.info(
                    f"POST query to service: {endpoint['individuals']} with body:"
                    + str(body)
                    + ": and header:"
                    + str(headers)
                )
                # On successful response, forward response
                if response.status == 200:
                    return await _service_response(response, None)
                elif response.status == 405:
                    raise Exception("We do not support downgrading POST to GET")
                else:
                    # HTTP errors
                    error = {
                        "service": endpoint["base"],
                        "queryParams": body,
                        "responseStatus": response.status,
                        "exists": None,
                    }

                    LOG.error(f"Query to {endpoint['base']} failed: {response}.")
                    return error
        except Exception as e:
            LOG.debug(f"Query error {e}.")
            web.HTTPInternalServerError(
                text="An error occurred while attempting to query services."
            )


async def find_query_endpoint(service: List[str], params):
    """Find endpoint for queries by parameters."""
    # since beaconV2 has multiple endpoints this method is used to define those endpoints from parameters
    endpoints = service

    # if length is 1 then beacon is v1
    raw_data = dict(parse.parse_qsl(params))
    if len(endpoints) <= 1 and raw_data.get("searchInInput") is None:
        return service[0]
    else:
        for endpoint in endpoints:
            if params == "filter" and "filtering_terms" in endpoint[0]:
                return endpoint
            if raw_data.get("searchInInput") is not None:
                if raw_data.get("searchInInput") in endpoint[0]:
                    if raw_data.get("id") != "0" and raw_data.get("id") is not None:
                        if (
                            raw_data.get("searchByInput") != ""
                            and raw_data.get("searchByInput") is not None
                        ):
                            url = list(endpoint)
                            url[0] += (
                                "/"
                                + raw_data.get("id")
                                + "/"
                                + raw_data.get("searchByInput")
                            )
                            endpoint = tuple(url)
                            return endpoint

                        url = list(endpoint)
                        url[0] += "/" + raw_data.get("id")
                        endpoint = tuple(url)
                        return endpoint
                    return endpoint


async def _service_response(response, ws):
    """Process response to web socket or HTTP."""
    result = await response.json()

    # LOG.debug(f"result: {result}")

    if ws is not None:
        # If the response comes from another aggregator, it's a list, and it needs to be broken down into dicts
        if isinstance(result, list):
            tasks = []
            # Prepare a websocket bundle return
            for sub_result in result:
                task = asyncio.ensure_future(ws_bundle_return(sub_result, ws))
                tasks.append(task)
            # Execute the bundle returns
            await asyncio.gather(*tasks)
        else:
            # The response came from a beacon and is a single object (dict {})
            # Send result to websocket
            return await ws.send_str(ujson.dumps(result, escape_forward_slashes=False))
    else:
        # Standard response
        return result


async def _get_request(session, service, params, headers, ws):
    """Get request for 1.0 beacons."""
    async with session.get(
        service[0], params=params, headers=headers, ssl=await request_security()
    ) as response:
        LOG.info(f"GET query to service: {service[0]}")
        # On successful response, forward response
        if response.status == 200:
            return await _service_response(response, ws)

        else:
            # HTTP errors
            error = {
                "service": service[0],
                "queryParams": params,
                "responseStatus": response.status,
                "exists": None,
            }
            LOG.error(f"Query to {service} failed: {response}.")
            if ws is not None:
                return await ws.send_str(
                    ujson.dumps(error, escape_forward_slashes=False)
                )
            else:
                return error


async def query_service(service, params, access_token, ws=None):
    """Query service with params."""
    LOG.debug("Querying service.")
    headers = {}
    if access_token:
        headers.update({"Authorization": f"Bearer {access_token}"})
    endpoint = await find_query_endpoint(service, params)
    # Pre-process query string into payload format
    if endpoint is not None:
        data = await pre_process_payload(endpoint[1], params)
        # Query service in a session
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    endpoint[0],
                    json=data,
                    headers=headers,
                    ssl=await request_security(),
                ) as response:
                    LOG.info(f"POST query to service: {endpoint}")
                    # On successful response, forward response
                    if response.status == 200:
                        return await _service_response(response, ws)
                    elif response.status == 405:
                        return await _get_request(
                            session, endpoint, params, headers, ws
                        )
                    else:
                        # HTTP errors
                        error = {
                            "service": endpoint[0],
                            "queryParams": params,
                            "responseStatus": response.status,
                            "exists": None,
                        }

                        LOG.error(f"Query to {service} failed: {response}.")
                        if ws is not None:
                            return await ws.send_str(
                                ujson.dumps(error, escape_forward_slashes=False)
                            )
                        else:
                            return error
            except Exception as e:
                LOG.debug(f"Query error {e}.")
                web.HTTPInternalServerError(
                    text="An error occurred while attempting to query services."
                )


async def ws_bundle_return(result, ws):
    """Create a bundle to be returned with websocket."""
    LOG.debug("Creating websocket bundle item.")

    # A simple function to bundle up websocket returns
    # when broken down from an aggregator response list
    return await ws.send_str(ujson.dumps(result, escape_forward_slashes=False))


async def validate_service_key(key):
    """Validate received service key."""
    LOG.debug("Validating service key.")

    for registry in CONFIG.registries:
        if key == registry.get("key"):
            # If a matching key is found, return true
            LOG.debug(f'Using service key of: {registry.get("url")}.')
            return True

    # If no matching keys were found, raise an exception
    raise web.HTTPUnauthorized(text="Unauthorized service key.")


async def clear_cache():
    """Clear cache of Beacons."""
    LOG.debug("Check if cache of Beacons exists.")

    try:
        cache = SimpleMemoryCache()
        if await cache.exists("beacon_urls"):
            LOG.debug("Found old cache.")
            await cache.delete("beacon_urls")
            LOG.debug("Cache has been cleared.")
        else:
            LOG.debug("No old cache found.")
        await cache.close()
    except Exception as e:
        LOG.error(f"Error at clearing cache: {e}.")


async def parse_results(results):
    """Break down lists in results if they exist."""
    LOG.debug("Parsing results for lists.")

    parsed_results = []

    # Check if the results contain any lists before processing
    if any(isinstance(result, list) for result in results):
        # Iterate through the results array [...]
        for result in results:
            # If this aggregator is aggregating aggregators, there will be lists in the results
            # Break the nested lists down into the same list [[{}, ...], {}, ...] --> [{}, {}, ...]
            if isinstance(result, list):
                for sub_result in result:
                    parsed_results.append(sub_result)
            else:
                # For direct Beacon responses, no processing is required [{}, ...] --> [{}, ...]
                parsed_results.append(result)
    else:
        # There were no lists in the results, so this processing can be skipped
        return results

    return parsed_results


def load_certs(ssl_context):
    """Load certificates for SSLContext object."""
    LOG.debug("Load certificates for SSLContext.")

    try:
        ssl_context.load_cert_chain(
            os.environ.get("PATH_SSL_CERT_FILE", "/etc/ssl/certs/cert.pem"),
            keyfile=os.environ.get("PATH_SSL_KEY_FILE", "/etc/ssl/certs/key.pem"),
        )
        ssl_context.load_verify_locations(
            cafile=os.environ.get("PATH_SSL_CA_FILE", "/etc/ssl/certs/ca.pem")
        )
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
        LOG.debug(
            f"Could not determine application security level ({level}), setting to default (0)."
        )

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
        LOG.debug(
            f"Could not determine request security level ({level}), setting to default (0)."
        )

    return ssl_context
