"""Update Endpoint."""

from ..utils.db_ops import db_get_service_details, db_update_service
from ..utils.utils import parse_service_info, http_request_info
from ..utils.logging import LOG


async def update_service_infos(request, db_pool):
    """Update service infos for registered services."""
    LOG.debug('Update service infos for registered services.')

    # A list of failures in case some updates failed
    failures = []

    services = []
    async with db_pool.acquire() as connection:
        # Get a listing of all registered services
        services = await db_get_service_details(connection)

        # Query each service and update their service info
        for service in services:
            try:
                # Request service info from given url
                service_info = await http_request_info(service['url'])
                # Parse and validate service info object
                req = {'url': service['url']}
                parsed_service_info = await parse_service_info(service['id'], service_info, req=req)
                # Update service info
                await db_update_service(connection, service['id'], parsed_service_info, service.get('contact_url', ''))
            except Exception as e:
                LOG.error(f'Update failed for {service["id"]}: {e}.')
                failures.append(service['id'])
                pass

    LOG.debug(f'Failed updates: {failures}.')
    # Return fails and total
    return len(failures), len(services)
