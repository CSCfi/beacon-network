"""Common Info Endpoint."""

from ..config import CONFIG
from ..utils.logging import LOG
from ..utils.utils import load_extension


async def get_info(host):
    """Return service info of self.

    Service ID is parsed from hostname to ensure that each service has a unique ID."""
    LOG.debug('Return service info.')

    service_info = {
        'id': '.'.join(reversed(host.split(','))),
        'name': CONFIG.name,
        'type': CONFIG.type,
        'description': CONFIG.description,
        'documentationUrl': CONFIG.documentation_url,
        'organization': CONFIG.organization,
        'contactUrl': CONFIG.contact_url,
        'apiVersion': CONFIG.api_version,
        'extension': await load_extension(CONFIG.extension)
    }

    return service_info
