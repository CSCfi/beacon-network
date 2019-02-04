"""Application Configuration."""

import os
from configparser import ConfigParser
from collections import namedtuple


def parse_config_file(path):
    """Parse configuration file."""
    config = ConfigParser()
    config.read(path)
    config_vars = {
        'registry': {
            'host_id': config.get('registry', 'host_id'),
            'db_host': config.get('registry', 'db_host'),
            'db_port': config.get('registry', 'db_port'),
            'db_user': config.get('registry', 'db_user'),
            'db_pass': config.get('registry', 'db_pass'),
            'db_name': config.get('registry', 'db_name')
        },
        'aggregator': {
            'host_id': config.get('aggregator', 'host_id'),
            'db_host': config.get('aggregator', 'db_host'),
            'db_port': config.get('aggregator', 'db_port'),
            'db_user': config.get('aggregator', 'db_user'),
            'db_pass': config.get('aggregator', 'db_pass'),
            'db_name': config.get('aggregator', 'db_name')
        }
    }
    return namedtuple("Config", config_vars.keys())(*config_vars.values())


CONFIG = parse_config_file(os.environ.get('CONFIG_FILE', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')))
