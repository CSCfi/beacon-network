"""Common Service Types Endpoint."""

from ..utils.logging import LOG


async def get_service_types():
    """Return GA4GH service types."""
    LOG.debug('Get service types.')
    return ['urn:ga4gh:registry', 'urn:ga4gh:aggregator', 'urn:ga4gh:beacon']
