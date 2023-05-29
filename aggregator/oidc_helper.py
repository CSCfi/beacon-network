import os
from typing import Optional

import aiohttp
from aioauth_client import OAuth2Client
from jwt import PyJWKSet

from .utils.logging import LOG

CALLBACK_ROUTE = "/cilogon/callback"


def get_deploy_url_from_env():
    if not "DEPLOY_URL" in os.environ:
        raise Exception("Missing environment variables for DEPLOY_URL")

    return os.environ["DEPLOY_URL"]


def get_oidc_redirect_uri_from_env():
    return get_deploy_url_from_env() + CALLBACK_ROUTE


def get_client_id():
    if "CLIENT_ID" not in os.environ:
        raise Exception("Missing environment variables for CLIENT_ID")

    return os.environ["CLIENT_ID"]


def get_issuer():
    return "https://test.cilogon.org"

async def get_oidc_client_from_env():
    SERVER = get_issuer()
    AUTHORIZE_URL = f"{SERVER}/authorize"
    TOKEN_URL = f"{SERVER}/oauth2/token"

    if not "CLIENT_SECRET" in os.environ:
        raise Exception("Missing environment variables for CLIENT_SECRET")

    jwkset: Optional[PyJWKSet] = None

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER}/.well-known/openid-configuration") as response:
            if response.status == 200:
                oidc_config = await response.json()

        async with session.get(oidc_config["jwks_uri"]) as response:
            if response.status == 200:
                jwks = await response.json()

                jwkset = PyJWKSet.from_dict(jwks)

    if not jwkset:
        raise Exception("JWKS set not constructed")

    return OAuth2Client(
        client_id=get_client_id(),
        client_secret=os.environ["CLIENT_SECRET"],
        base_url=SERVER,
        authorize_url=AUTHORIZE_URL,
        access_token_url=TOKEN_URL,
        logger=LOG
    ), jwkset
