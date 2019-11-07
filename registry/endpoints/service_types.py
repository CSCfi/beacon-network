"""Common Service Types Endpoint."""

from ..utils.logging import LOG


async def get_service_types():
    """Return GA4GH service types."""
    LOG.debug('Get service types.')
    return ['org.ga4gh:service-registry', 'org.ga4gh:beacon-aggregator', 'org.ga4gh:beacon']
