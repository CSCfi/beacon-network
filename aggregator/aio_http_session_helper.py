import os

from cryptography import fernet


def get_session_secret_from_env():
    if not "SESSION_SECRET" in os.environ:
        raise Exception("Missing environment variables for SESSION_SECRET")

    return fernet.Fernet(os.environ["SESSION_SECRET"])
