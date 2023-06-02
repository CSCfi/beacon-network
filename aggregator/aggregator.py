"""Beacon Aggregator API."""
import os
import sys
from typing import Optional, List

import aiohttp.web
import aiohttp_session
import jwt
from aioauth_client import OAuth2Client
from aiohttp import web
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from aiohttplimiter import Limiter, default_keyfunc
from cryptography.hazmat.primitives import serialization
from jwt import PyJWKSet

from aggregator.aio_http_session_helper import get_session_secret_from_env
from aggregator.constants import SESSION_KEY_CILOGON_TOKEN
from aggregator.endpoints.endpoint import BeaconEndpoint
from aggregator.jwt_helper import get_private_key_from_env, generate_beacon_network_jwt, OUR_KID
from aggregator.oidc_helper import (
    get_oidc_client_from_env,
    CALLBACK_ROUTE,
    get_oidc_redirect_uri_from_env,
    get_deploy_url_from_env,
    get_client_id,
    get_issuer,
)
from .config import CONFIG
from .endpoints.info import get_info
from .endpoints.query import post_beacon_query
from .utils.logging import LOG

routes = web.RouteTableDef()

limiter = Limiter(keyfunc=default_keyfunc)

# for a demonstration system 10/s is a decent rate limit for all our APIs
DEFAULT_RATE_LIMIT = "10/second"


# The keys into our AIO HTTP requests
# For some reason the documented AppKey is not working (yet? version?)

# static_folder_key = web.AppKey("static_folder", str)
static_folder_key = "static_folder"
jwt_private_key_key = "jwt_private_key"
oidc_client_key = "oidc_client"
oidc_server_jwks_key = "oidc_server_jwks"


@routes.post("/cilogon/auth")
@limiter.limit(DEFAULT_RATE_LIMIT)
async def auth(request: aiohttp.web.Request):
    """Initiate OIDC flow."""
    LOG.debug("POST /auth received.")

    authorize_url = request.app[oidc_client_key].get_authorize_url(
        scope="openid email profile", redirect_uri=get_oidc_redirect_uri_from_env()
    )

    LOG.info("Starting OIDC flow to URL '%s'", authorize_url)

    return web.HTTPTemporaryRedirect(authorize_url)


@routes.post("/cilogon/logout")
@limiter.limit("10/second")
async def auth(request: aiohttp.web.Request):
    """Logout of OIDC."""

    session = await aiohttp_session.get_session(request)

    session.invalidate()

    response = web.HTTPSeeOther("/")

    response.del_cookie("logged_in_name")
    response.del_cookie("logged_in_email")
    response.del_cookie("logged_in_sub")
    response.del_cookie("logged_in_network_beacon_jwt")

    return response


@routes.get(CALLBACK_ROUTE)
@limiter.limit("10/second")
async def callback(request: aiohttp.web.Request):
    """
    Get the code from an OIDC flow (via callback) and then exchange that for a token.
    """
    LOG.debug("GET /callback received.")

    code = request.query["code"]

    oidc_client: OAuth2Client = request.app[oidc_client_key]

    LOG.debug("OIDC client client id '%s'", oidc_client.client_id)
    LOG.debug("OIDC client access token url '%s'", oidc_client.access_token_url)

    # do a token exchange of the code for real tokens
    _, tokens = await oidc_client.get_access_token(
        code, redirect_uri=get_oidc_redirect_uri_from_env()
    )

    # we downloaded the CILogon JWKS on service start
    oidc_server_jwks: PyJWKSet = request.app[oidc_server_jwks_key]

    # OIDC/ID TOKEN JWT handling
    # importantly we cannot trust some of the fields here (i.e. alg)
    id_token = tokens["id_token"]

    header = jwt.get_unverified_header(id_token)

    LOG.debug(header)

    if header["alg"] not in ["RS256", "RS384", "RS512"]:
        raise Exception("Algorithm from OIDC flow was not white listed")

    alg = header["alg"]
    kid = header["kid"]

    decoded = jwt.decode(
        id_token,
        oidc_server_jwks[kid].key,
        algorithms=[alg],
        audience=get_client_id(),
        issuer=get_issuer(),
        options={},
    )

    LOG.debug(decoded)

    # our source of authority (i.e. our issuer for tokens) is where we are deployed i.e. https://beacon.umccr.org
    deploy_url = get_deploy_url_from_env()

    endpoints: List[BeaconEndpoint] = CONFIG.endpoints

    # use the claims from the CILogon id token to create a new JWT
    network_beacon_jwt = generate_beacon_network_jwt(
        deploy_url,
        # we want the audience of the new token to have the server names of all endpoints in the network
        list(map(lambda n: n['base'], endpoints)),
        decoded,
        request.app[jwt_private_key_key],
        OUR_KID,
    )

    # now store the new JWT in our encrypted session state
    session = await aiohttp_session.new_session(request)
    session[SESSION_KEY_CILOGON_TOKEN] = network_beacon_jwt

    # response sending them back to the dashboard page but also set some useful cookies for the frontend
    response = web.HTTPTemporaryRedirect("/dashboard")
    response.set_cookie("logged_in_name", decoded["name"])
    response.set_cookie("logged_in_email", decoded["email"])
    response.set_cookie("logged_in_sub", decoded["sub"])
    response.set_cookie("logged_in_network_beacon_jwt", network_beacon_jwt)

    return response


@routes.get("/service-info")
async def info(request: aiohttp.web.Request):
    """Return service info."""
    LOG.debug("GET /info received.")
    return web.json_response(await get_info(request.host))


@routes.get("/.well-known/openid-configuration")
@limiter.limit("10/second")
async def well_known_openid_configuration(request: aiohttp.web.Request):
    deploy_url = get_deploy_url_from_env()

    return web.json_response(
        {"issuer": deploy_url, "jwks_uri": f"{deploy_url}/.well-known/jwks.json"}
    )


@routes.get("/.well-known/jwks.json")
@limiter.limit("10/second")
async def well_known_jwks(request: aiohttp.web.Request):
    public_key = request.app[jwt_private_key_key].public_key()

    # Get the public key components
    x = public_key.public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    )

    from base64 import urlsafe_b64encode

    x_base64url = urlsafe_b64encode(x).rstrip(b"=").decode("utf-8")

    return web.json_response(
        {"keys": [{"kid": OUR_KID, "kty": "OKP", "crv": "Ed25519", "x": x_base64url}]}
    )


@routes.post("/query")
@limiter.limit("10/second")
async def query_post(request: aiohttp.web.Request):
    """Forward variant query to Beacons."""
    LOG.debug("POST /query received.")

    # Use standard synchronous http
    # Send request for processing
    response = await post_beacon_query(request)

    # Return results
    return web.json_response(response)


@routes.get("/{tail:.*}", name="index")
@limiter.limit("10/second")
async def index(request):
    """Catch all file handler endpoint.

    Returns the content of a file if it exists, else the contents of index.html
    """
    LOG.debug("Catch all file handler endpoint.")

    # the static folder is configured to tell us the absolute path of the front end files
    # we want to serve the files up in a way that is suitable for React/Vuejs etc
    static_folder = request.app[static_folder_key]

    if request.path != "/" and request.path != "/index.html":
        # check if the file (say /assets/myfile.jpg) actually exists on the disk underneath
        # our static folder root
        file_path = sanitize_path(
            request.app[static_folder_key], request.path[1:], True
        )

        # if it exists then serve it up
        if file_path:
            # because we are serving up vitejs built react that uses asset checksums - we can be
            # very aggressive on the caching of these - even in dev
            return web.FileResponse(
                file_path,
                headers={
                    "Cache-Control": "public, max-age=31536000",
                    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                },
            )

    # otherwise - to best support routing in React/Vuejs - we serve up the index.html
    # for all other requests

    # because our index.html does not have an asset checksum - we make sure it is not cached
    return web.FileResponse(
        os.path.join(static_folder, "index.html"),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Expires": "0",
        },
    )


def sanitize_path(base_path: str, filename: str, subdir_allowed: bool) -> Optional[str]:
    """
    Path sanitiser for wildcard index serving

    Returns the absolute path of the filename joined to the base_path - assuming the
    absolute path eventually ends up as a subfolder of the base. i.e. prevents "../.." shenanigans
    by the "filename"

    If the file at the sanitized path actually exists - then return the path
    If there is no file - then return None
    """
    # basepath should be absolute. Example: '/app/public'
    # filename is relative to base. Example: 'image.jpg' or 'subdir1/subdir2/image.jpg' when subdir_allowed=True

    filepath = os.path.join(base_path, filename)
    # e.g. if filepath can look like '/app/public/../../usr/secret.txt
    real_filepath = os.path.realpath(filepath)  # resolves symbolic links and /../
    # then real_filepath will look like '/usr/secret.txt'

    if subdir_allowed:
        prefix = os.path.commonpath((base_path, real_filepath))
    else:
        prefix = os.path.dirname(real_filepath)  # directory of the file

    if prefix == base_path and os.path.isfile(real_filepath):
        return real_filepath
    else:
        return None


# FOR HGPP/BioCommons deployment we are relying on a pure POST API

# @routes.get("/query")
# async def query(request: aiohttp.web.Request):
#     """Forward variant query to Beacons."""
#     LOG.debug("GET /query received.")
#
#     # For websocket
#     connection_header = request.headers.get("Connection", "default").lower().split(",")  # break down if multiple items
#     connection_header = [value.strip() for value in connection_header]  # strip spaces
#
#     if "upgrade" in connection_header and request.headers.get("Upgrade", "default").lower() == "websocket":
#         # Use asynchronous websocket connection
#         # Send request for processing
#         websocket = await send_beacon_query_websocket(request)
#         # Return websocket connection
#         return websocket
#     else:
#         # Use standard synchronous http
#         # Send request for processing
#         response = await send_beacon_query(request)
#
#         # Return results
#         return web.json_response(response)
#
#
# @routes.delete("/cache")
# async def cache(request: aiohttp.web.Request):
#     """Invalidate cached Beacons."""
#     LOG.debug("DELETE /beacons received.")
#
#     # Send request for processing
#     await invalidate_cache()
#
#     # Return confirmation
#     return web.Response(text="Cache has been deleted.")


# def set_cors(app):
#     """Set CORS rules."""
#     LOG.debug(f"Applying CORS rules: {CONFIG.cors}.")
#     # Configure CORS settings, allow all domains
#     cors = aiohttp_cors.setup(
#         app,
#         defaults={
#             CONFIG.cors: aiohttp_cors.ResourceOptions(
#                 allow_credentials=True,
#                 expose_headers="*",
#                 allow_headers="*",
#             )
#         },
#     )
#     # Apply CORS to endpoints
#     for route in list(app.router.routes()):
#         cors.add(route)


async def response_headers(_, res):
    """Modify response headers before returning response."""
    res.headers["Server"] = "Australian-BioCommons-Beacon-Network"


async def init_app(static_folder: str):
    """Initialise the web server."""
    LOG.info("Initialising web server.")

    # removed api_key() from middlewares
    app = web.Application(middlewares=[])
    app.on_response_prepare.append(response_headers)
    app.router.add_routes(routes)

    # pass through to the rest of the app where the frontend files live
    app[static_folder_key] = static_folder

    # pick up some necessary (secret) settings from our environment and turn into real objects
    pk = get_private_key_from_env()

    # the private key we are using for JWT signing
    app[jwt_private_key_key] = pk

    # configured OIDC client
    oc, oc_jwks = await get_oidc_client_from_env()

    app[oidc_client_key] = oc
    app[oidc_server_jwks_key] = oc_jwks

    # setup a secure session to hold our JWTs (only used by the backend for queries - not for frontend use)
    aiohttp_session.setup(app, EncryptedCookieStorage(get_session_secret_from_env()))

    # For the use of the HGPP UI there is no need for CORS - revisit if there is another use case for CORS
    # if CONFIG.cors:
    #    set_cors(app)

    return app


def main():
    """Run the web server."""
    LOG.setLevel("DEBUG")

    LOG.info("Starting server.")

    LOG.info(f"Location of main Python file is {__file__}")

    for k, v in os.environ.items():
        if not k.startswith("AWS_") and not k.startswith("ECS_"):
            LOG.info(f"{k}={v}")

    # where is our actual server python file - we know the UI is relative to us
    root_py_path = os.path.dirname(os.path.abspath(__file__))

    # find the absolute path of where the UI files should be
    abs_static_folder = os.path.realpath(os.path.join(root_py_path, "..", "ui", "dist"))

    if os.path.isdir(abs_static_folder):
        if not os.path.isfile(os.path.join(abs_static_folder, "index.html")):
            LOG.error(
                "Needs to be able to read the file ../ui/dist/index.html - have you built the frontend?"
            )
            sys.exit(1)
        else:
            web.run_app(
                init_app(abs_static_folder),
                host=CONFIG.host,
                port=CONFIG.port,
                shutdown_timeout=0,
            )
            # ssl_context=application_security())
    else:
        LOG.error("Missing ui/dist")
        sys.exit(1)


if __name__ == "__main__":
    if sys.version_info < (3, 6):
        LOG.error("beacon-network:aggregator requires python 3.6 or higher")
        sys.exit(1)

    # we use a stable JWT private key from the env... if we need to regenerate it - this is how
    # (but in normally operation this code is disabled)
    # print(generate_private_key_for_env())

    main()
