import os
from typing import List

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from .utils.logging import LOG


def generate_beacon_network_jwt(
    issuer: str,
    other_sites: List[str],
    cilogon_decoded: any,
    target_private_key: Ed25519PrivateKey,
    target_kid: str,
):
    # the basic payload is just really proof the person has logged in via CILogon
    payload = {
        "iss": issuer,
        "sub": cilogon_decoded["sub"],
        "exp": cilogon_decoded["exp"],
        "aud": [issuer] + other_sites,
    }

    if "groups" in cilogon_decoded:
        g: List[str] = cilogon_decoded["groups"]

        if "HGPP Researcher by Organisation" in g:
            payload["researcher"] = True

    LOG.debug(payload)

    # sign the JWT with the private key
    new_jwt_token = jwt.encode(
        payload, target_private_key, algorithm="EdDSA", headers={"kid": target_kid}
    )

    return new_jwt_token


def test_beacon_network_jwt_create_and_decode():
    jwt = generate_beacon_network_jwt(
        "https://fake.site.com",
        ["https://fake2.site.com"],
        {
            "sub": "http://cilogon.org/serverA/users/46001501",
            "iss": "https://test.cilogon.org",
            "groups": [
                "CO:members:all",
                "CO:members:active",
                "CO:COU:UMCCR grp moderator:members:active",
                "CO:COU:UMCCR grp moderator:members:all",
                "CO:COU:University of Melbourne Centre for Cancer Research :admins",
                "Elsa Data dev localhost",
                "OIDC mgrs",
                "CO:admins",
            ],
            "given_name": "Andrew",
            "aud": "cilogon:/client_id/2f3284e8fb5c3d3d956448c316aec43c",
            "auth_time": 1685325378,
            "name": "Andrew Patterson",
            "exp": 1685326279,
            "family_name": "Patterson",
            "iat": 1685325379,
            "email": "andrew@patto.net",
            "jti": "https://test.cilogon.org/oauth2/idToken/value",
        },
        get_private_key_from_env(),
        "AKID",
    )

    print(jwt)


def get_private_key_from_env():
    if "JWT_PEM" not in os.environ:
        raise Exception("Missing environment variable JWT_PEM")

    # env variables must be strings... we will have had to do some magic to get the \n into the env string
    # but otherwise it should just be a straight decode from ASCII to the byte array we need
    jwt_pem = os.environ["JWT_PEM"]

    # there are some scenarios (incorrect editing Secrets Manager secret) where the \n comes into the string
    # as the escape character sequence... due to the nature of the content of a PEM - there is very little
    # danger in doing this no matter what
    jwt_pem = jwt_pem.replace("\\n", "\n")

    jwt_pem_bytes = bytes(jwt_pem, "ascii")

    private_key = serialization.load_pem_private_key(
        jwt_pem_bytes, password=None  # No password protection
    )

    # verify that the loaded key is an Ed25519 private key
    if not isinstance(private_key, Ed25519PrivateKey):
        raise ValueError("The provided key is not an Ed25519 private key.")

    return private_key


def generate_private_key_for_env():
    # Generate a new Ed25519 private key
    private_key = Ed25519PrivateKey.generate()

    # Convert the private key to PEM format
    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    private_key_pem_as_env_string = private_key_pem.decode("ascii")

    # this is a technique for bash the allows insertion of escape sequences in env strings
    return f"export JWT_PEM=$'{private_key_pem_as_env_string}'"


# # Create a JWT payload
#
#
#
