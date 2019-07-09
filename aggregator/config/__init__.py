"""Aggregator Configuration."""

import os
from configparser import ConfigParser
from collections import namedtuple
from distutils.util import strtobool


def parse_config_file(path):
    """Parse configuration file."""
    config = ConfigParser()
    config.read(path)
    config_vars = {
        'host': os.environ.get('HOST', config.get('app', 'host')) or '0.0.0.0',
        'port': int(os.environ.get('PORT', config.get('app', 'port')) or 8080),
        'registries': config.get('app', 'registries') or '',
        'beacons': bool(strtobool(config.get('app', 'beacons'))) or True,
        'aggregators': bool(strtobool(config.get('app', 'aggregators'))) or False,
        'name': config.get('info', 'name'),
        'type': config.get('info', 'type'),
        'description': config.get('info', 'description'),
        'documentation_url': config.get('info', 'documentation_url'),
        'organization': config.get('info', 'organization'),
        'contact_url': config.get('info', 'contact_url'),
        'api_version': config.get('info', 'api_version'),
        'version': config.get('info', 'version'),
        'extension': config.get('info', 'extension')
    }
    return namedtuple("Config", config_vars.keys())(*config_vars.values())


CONFIG = parse_config_file(os.environ.get('CONFIG_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')))
