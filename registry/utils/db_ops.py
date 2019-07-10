"""Database Operations."""

import json

from aiohttp import web

from .logging import LOG
from .utils import construct_json, generate_service_key


async def db_check_service_id(connection, id):
    """Check if service id exists."""
    LOG.debug('Querying database for service id.')
    try:
        # Database query
        query = """SELECT name FROM services WHERE id=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify availability of service ID.')
    else:
        if len(response) > 0:
            LOG.debug(f'Found service "{response}" for ID "{id}".')
            return True
        else:
            LOG.debug(f'No conflicting services found for ID "{id}".')
            return False


async def db_store_service_key(connection, id, service_key):
    """Store generated service key."""
    LOG.debug('Store service key.')
    try:
        # Database commit occurs on transaction closure
        async with connection.transaction():
            await connection.execute("""INSERT INTO service_keys (service_id, service_key)
                                     VALUES ($1, $2)""",
                                     id, service_key)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to store service key.')


async def db_update_service_key(connection, old_id, new_id):
    """Update stored service key's service id."""
    LOG.debug('Update service key\'s service id.')
    try:
        await connection.execute("""UPDATE service_keys SET service_id=$1 WHERE service_id=$2""",
                                 new_id, old_id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to update service key\'s service id.')


async def db_delete_service_key(connection, id):
    """Delete stored service key."""
    LOG.debug('Delete service key.')
    try:
        await connection.execute("""DELETE FROM service_keys WHERE service_id=$1""", id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to delete service key.')


async def db_register_service(connection, service, email):
    """Register new service at host."""
    LOG.debug('Register new service.')
    try:
        # Database commit occurs on transaction closure
        async with connection.transaction():
            await connection.execute("""INSERT INTO services (id, name, type, description, url, contact_url,
                                     api_version, service_version, extension, email, created_at, updated_at)
                                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())""",
                                     service['id'], service['name'], service['type'],
                                     service['description'], service['url'], service['contact_url'],
                                     service['api_version'], service['service_version'], json.dumps(service['extension']), email)
            # If service registration was successful, generate and store a service key
            service_key = await generate_service_key()
            await db_store_service_key(connection, service['id'], service_key)
            return service_key  # return service key to registrar for later use

    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to register service.')


async def db_get_service_details(connection, id=None, service_type=None, api_version=None):
    """Get all or selected service details."""
    LOG.debug('Get service details.')
    services = []

    # For handling prepared parameters
    sql_id = id if id is not None else True
    sql_service_type = service_type if service_type is not None else True
    sql_api_version = api_version if api_version is not None else True

    try:
        # Database query
        query = f"""SELECT id, name, type, description, url, contact_url, api_version,
                    service_version, extension, created_at, updated_at
                    FROM services
                    WHERE {'id=$1' if id is not None else '$1'}
                    AND {'type=$2' if service_type is not None else '$2'}
                    AND {'api_version=$3' if api_version is not None else '$3'}"""
        statement = await connection.prepare(query)
        response = await statement.fetch(sql_id, sql_service_type, sql_api_version)
        if len(response) > 0:
            for record in response:
                # Build JSON response
                service = await construct_json(record)
                if id:
                    # If user specified ID, database gave a single response -> return it
                    return service
                else:
                    # If user didn't specify ID, get all services -> combine all and return
                    services.append(service)
            return services
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to get service details.')

    # Didn't enter len(response)>0 block
    raise web.HTTPNotFound(text='Service(s) not found.')


async def db_delete_services(connection, id=None):
    """Delete all or specified service(s)."""
    LOG.debug('Delete service(s).')

    try:
        await connection.execute("""DELETE FROM services WHERE id=$1""", id)
        await db_delete_service_key(connection, id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to delete service(s).')


async def db_update_service(connection, id, service, email):
    """Update service."""
    LOG.debug('Update service.')

    # Check if user wants to change service id
    if not id == service['id']:
        # Check if desired service ID is taken
        service_id = await db_check_service_id(connection, service['id'])
        if service_id:
            # Chosen service ID is taken
            raise web.HTTPConflict(text='Service ID is taken.')

    # Apply updates
    try:
        await connection.execute("""UPDATE services SET id=$1, name=$2, type=$3, description=$4,
                                 url=$5, contact_url=$6, api_version=$7, service_version=$8, extension=$9,
                                 email=$10, updated_at=NOW()
                                 WHERE id=$11""",
                                 service['id'], service['name'], service['type'],
                                 service['description'], service['url'], service['contact_url'],
                                 service['api_version'], service['service_version'], json.dumps(service['extension']),
                                 email, service['id'])
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to update service details.')


async def db_update_sequence(connection, id, updates, email):
    """Initiate update sequence."""
    LOG.debug('Initiate update sequence.')

    # Carry out operations within a transaction to avoid conflicts
    async with connection.transaction():
        # First update the service info, if that passes, update the service id at service_keys if it changed
        await db_update_service(connection, id, updates, email)
        # Update service id at service_keys in case it changed
        await db_update_service_key(connection, id, updates['id'])


async def db_verify_service_key(connection, service_id=None, service_key=None):
    """Check if service id exists."""
    LOG.debug('Querying database to verify Beacon-Service-Key.')
    try:
        # Database query
        query = """SELECT service_id FROM service_keys WHERE service_id=$1 AND service_key=$2"""
        statement = await connection.prepare(query)
        response = await statement.fetch(service_id, service_key)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify Beacon Service Key.')
    else:
        if len(response) == 0:
            LOG.debug('Provided service key is unauthorised or service id is wrong.')
            raise web.HTTPUnauthorized(text='Unauthorised service key or wrong service id.')
        LOG.debug('Service key is authorised.')


async def db_verify_api_key(connection, api_key):
    """Check if provided api key for registration is authorised."""
    LOG.debug('Querying database to verify "Authorization" API key.')
    try:
        # Database query
        query = """SELECT comment FROM api_keys WHERE api_key=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(api_key)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify "Authorization" API key.')
    else:
        if len(response) == 0:
            LOG.debug('Provided api key is unauthorised.')
            raise web.HTTPUnauthorized(text='Unauthorised api key.')
        LOG.debug('Api key is authorised.')
