"""Update Endpoint."""

import asyncio
import uvloop

from ..utils.db_ops import db_get_service_details, db_update_service
from ..utils.utils import parse_service_info, http_request_info
from ..utils.logging import LOG

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def update_service_infos(request, db_pool):
    """Update service infos for registered services."""
    LOG.debug('Update service infos for registered services.')

    tasks = []
    failures = []
    services = []

    async with db_pool.acquire() as connection:
        # Get a listing of all registered services
        services = await db_get_service_details(connection)

        # Generate async task queue
        for service in services:
            task = asyncio.ensure_future(update_sequence(service, db_pool))
            tasks.append(task)

    # Initiate async queue
    results = await asyncio.gather(*tasks)
    # Filter successes away
    failures = [service for service in results if service is not None]

    LOG.debug(f'Failed updates: {failures}.')
    # Return fails and total
    return len(failures), len(services)


async def update_sequence(service, db_pool):
    """Update sequence tasks."""
    LOG.debug('Updating service info.')
    try:
        # Request service info from given url
        service_info = await http_request_info(service['url'])
        # Parse and validate service info object
        req = {'url': service['url']}
        parsed_service_info = await parse_service_info(service['id'], service_info, req=req)
        # Update service info
        async with db_pool.acquire() as connection:
            await db_update_service(connection, service['id'], parsed_service_info, service.get('contact_url', ''))
    except Exception as e:
        LOG.error(f'Update failed for {service["id"]}: {e}.')
        return service['id']
