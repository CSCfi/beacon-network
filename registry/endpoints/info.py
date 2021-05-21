"""Common Info Endpoint."""

import datetime

from ..config import CONFIG
from ..utils.logging import LOG


async def get_info(host):
    """Return service info of self.

    Service ID is parsed from hostname to ensure that each service has a unique ID.
    """
    LOG.debug("Return service info.")

    service_info = {
        "id": ".".join(reversed(host.split("."))),
        "name": CONFIG.name,
        "type": {"group": CONFIG.type_group, "artifact": CONFIG.type_artifact, "version": CONFIG.type_version},
        "description": CONFIG.description,
        "organization": {"name": CONFIG.organization, "url": CONFIG.organization_url},
        "contactUrl": CONFIG.contact_url,
        "documentationUrl": CONFIG.documentation_url,
        "createdAt": CONFIG.create_time,
        "updatedAt": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "environment": CONFIG.environment,
        "version": CONFIG.version,
    }

    return service_info
