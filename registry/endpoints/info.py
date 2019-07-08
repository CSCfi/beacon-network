"""Common Info Endpoint."""

from utils.logging import LOG
from utils.db_ops import db_get_service_details


async def get_info(host_id, db_pool):
    """Return service info of self."""
    LOG.debug('Get service info of self.')

    # Take connection from the database pool
    async with db_pool.acquire() as connection:
        # Fetch service info from database
        response = await db_get_service_details(connection, id=host_id)

    return response
