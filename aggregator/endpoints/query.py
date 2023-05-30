"""Aggregator Query Endpoint."""

import asyncio
from typing import List

import aiohttp
import uvloop
from aiohttp import web
from jsonschema import Draft7Validator, validators

from .endpoint import BeaconEndpoint
from ..config import CONFIG
from ..schemas import load_schema
from ..utils.logging import LOG
from ..utils.utils import (
    get_access_token,
    parse_results,
    post_query_service,
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())





# async def send_beacon_query(request: aiohttp.web.Request):
#     """Send Beacon queries and respond synchronously."""
#     LOG.debug("Normal response (sync).")
#
#     tasks = []  # requests to be done
#     services = await get_services(request.host)  # service urls (beacons, aggregators) to be queried
#     access_token = await get_access_token(request)  # Get access token if one exists
#
#     print(access_token)
#
#     for service in services:
#         # Generate task queue
#         if "&filters=filter" in request.query_string:
#             task = asyncio.ensure_future(
#                 query_service(
#                     service,
#                     request.query_string.replace("&filters=filter", ""),
#                     access_token,
#                 )
#             )
#             tasks.append(task)
#             task = asyncio.ensure_future(query_service(service, "filter", access_token))
#             tasks.append(task)
#         else:
#             task = asyncio.ensure_future(
#                 query_service(service, request.query_string, access_token)
#             )
#             tasks.append(task)
#     # Prepare and initiate co-routines
#     results = await asyncio.gather(*tasks)
#
#     # Check if this aggregator is aggregating aggregators
#     # Aggregators return lists instead of objects, so they need to be broken down into a single list
#     if CONFIG.aggregators:
#         results = await parse_results(results)
#
#     return results

def extend_with_default(validator_class):
    """Include default values present in JSON Schema.

    Source: https://python-jsonschema.readthedocs.io/en/latest/faq/#why-doesn-t-my-schema-s-default-property-set-the-default-on-my-instance
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator,
            properties,
            instance,
            schema,
        ):
            yield error

    return validators.extend(
        validator_class,
        {"properties": set_defaults},
    )


DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


async def post_beacon_query(request: aiohttp.web.Request):
    """Post Beacon queries and respond synchronously."""
    LOG.debug("Normal response (sync), inside .............post_beacon_query")

    schema = load_schema("beacon_body")
    request_json_body = await request.json()

    LOG.debug(request_json_body)

    #try:
    #    LOG.debug("Validate against JSON schema")
    #
    #    DefaultValidatingDraft7Validator(schema).validate(request_json_body)
    #except ValidationError as e:
    #    LOG.debug(f"ERROR: Could not validate -> {request_json_body}, {request.host}, {e.message}")
    #    raise web.HTTPBadRequest(text=f"Could not validate request body: {e.message}")

    # build a list of downstream beacon queries to be done in parallel
    tasks = []

    endpoints: List[BeaconEndpoint] = CONFIG.endpoints

    LOG.debug(endpoints)

    # get an access token if we have one (either from client or in our session)
    access_token = await get_access_token(request)

    for endpoint in endpoints:
        # Generate task for queue
        task = asyncio.ensure_future(
            post_query_service(endpoint, access_token, request_json_body)
        )
        tasks.append(task)

    # Prepare and initiate co-routines
    results = await asyncio.gather(*tasks)

    return results


# async def send_beacon_query_websocket(request: aiohttp.web.Request):
#     """Send Beacon queries and respond asynchronously via websocket."""
#     LOG.debug("Websocket response (async).")
#     # Prepare websocket connection
#     ws = web.WebSocketResponse()
#     await ws.prepare(request)
#
#     # Task variables
#     tasks = []  # requests to be done
#     services = await get_services(
#         request.host
#     )  # service urls (beacons, aggregators) to be queried
#     access_token = await get_access_token(request)  # Get access token if one exists
#
#     for service in services:
#         # Generate task queue
#         LOG.debug(f"Query service: {service}")
#         if "&filters=filter" in request.query_string:
#             task = asyncio.ensure_future(
#                 query_service(
#                     service,
#                     request.query_string.replace("&filters=filter", ""),
#                     access_token,
#                     ws=ws,
#                 )
#             )
#             tasks.append(task)
#             task = asyncio.ensure_future(
#                 query_service(service, "filter", access_token, ws=ws)
#             )
#             tasks.append(task)
#         else:
#             task = asyncio.ensure_future(
#                 query_service(service, request.query_string, access_token, ws=ws)
#             )
#             tasks.append(task)
#     # Prepare and initiate co-routines
#     await asyncio.gather(*tasks)
#     # Close websocket after all results have been sent
#     await ws.close()
#
#     return ws
