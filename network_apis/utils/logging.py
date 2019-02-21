"""Logging formatting."""

import os
import logging

from distutils.util import strtobool

formatting = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(module)s | %(funcName)s: %(message)s'
logging.basicConfig(level=logging.DEBUG if bool(strtobool(os.environ.get('DEBUG', 'False'))) else logging.INFO, format=formatting)
LOG = logging.getLogger("bn")
