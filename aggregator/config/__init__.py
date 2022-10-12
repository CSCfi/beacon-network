"""Aggregator Configuration."""

import os
import ujson

from configparser import ConfigParser
from collections import namedtuple
from distutils.util import strtobool

from ..utils.logging import LOG


def load_json(json_file):
    json_file = os.environ.get("CONFIG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "registries.json"))
    """Load data from an external JSON file."""
    LOG.debug(f"Loading data from file: {json_file}.")
    LOG.info(f"Loading data from registries json file:"+json_file)
    data = {}
    if os.path.isfile(json_file):
        with open(json_file, "r") as contents:
            data = ujson.loads(contents.read())
    else:
        LOG.info("could not find registries json file.....:"+json_file)
    return data


def parse_config_file(path):
    """Parse configuration file."""
    LOG.debug("Reading configuration file.")
    LOG.info("Reading configuration file:"+path)

    config = ConfigParser()
    config.read(path)

    LOG.info("app registries.......:"+config.get("app", "registries"))
    LOG.info("json from app registries....:"+str(load_json(config.get("app", "registries"))))
    config_vars = {
        "host": os.environ.get("APP_HOST", config.get("app", "host")) or "0.0.0.0",
        "port": int(os.environ.get("APP_PORT", config.get("app", "port")) or 8080),
        "registries": load_json(config.get("app", "registries")) or [],
        "beacons": bool(strtobool(config.get("app", "beacons"))) or True,
        "aggregators": bool(strtobool(config.get("app", "aggregators"))) or False,
        "cors": os.environ.get("APP_CORS", config.get("app", "cors")),
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
    }
    return namedtuple("Config", config_vars.keys())(*config_vars.values())

LOG.info("CONFIG_FILE:"+os.environ.get("CONFIG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")))
CONFIG = parse_config_file(os.environ.get("CONFIG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")))
