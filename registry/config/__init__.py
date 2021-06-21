"""Registry Configuration."""

import os

from configparser import ConfigParser
from collections import namedtuple
from distutils.util import strtobool

from ..utils.logging import LOG


def parse_config_file(path):
    """Parse configuration file."""
    LOG.debug("Reading configuration file.")
    config = ConfigParser()
    config.read(path)
    config_vars = {
        "host": os.environ.get("APP_HOST", config.get("app", "host")) or "0.0.0.0",
        "port": int(os.environ.get("APP_PORT", config.get("app", "port")) or 8080),
        "db_host": os.environ.get("DB_HOST", config.get("app", "db_host")) or "localhost",
        "db_port": int(os.environ.get("DB_PORT", config.get("app", "db_port")) or 5432),
        "db_user": os.environ.get("DB_USER", config.get("app", "db_user")) or "user",
        "db_pass": os.environ.get("DB_PASS", config.get("app", "db_pass")) or "pass",
        "db_name": os.environ.get("DB_NAME", config.get("app", "db_name")) or "db",
        "api_otp": bool(strtobool(os.environ.get("API_OTP", config.get("app", "api_otp")))) or True,
        "cors": os.environ.get("APP_CORS", config.get("app", "cors")) or "*",
        "name": config.get("info", "name"),
        "type_group": config.get("info", "type_group"),
        "type_artifact": config.get("info", "type_artifact"),
        "type_version": config.get("info", "type_version"),
        "description": config.get("info", "description"),
        "documentation_url": config.get("info", "documentation_url"),
        "organization": config.get("info", "organization"),
        "organization_url": config.get("info", "organization_url"),
        "contact_url": config.get("info", "contact_url"),
        "version": config.get("info", "version"),
        "create_time": config.get("info", "create_time"),
        "environment": config.get("info", "environment"),
        "testEnv": bool(strtobool(config.get("app", "test"))) or False
    }
    return namedtuple("Config", config_vars.keys())(*config_vars.values())


CONFIG = parse_config_file(os.environ.get("CONFIG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")))
