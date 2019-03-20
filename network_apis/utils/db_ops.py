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
            return True
        else:
            return False


async def db_check_organisation_id(connection, id):
    """Check if organisation id exists."""
    LOG.debug('Querying database for organisation id.')
    try:
        # Database query
        query = """SELECT name FROM organisations WHERE id=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify availability of organisation ID.')
    else:
        if len(response) > 0:
            return True
        else:
            return False


async def db_register_organisation(connection, organisation):
    """Register new organisation at host."""
    LOG.debug('Register organisation if it doesn\'t exist.')
    try:
        await connection.execute("""INSERT INTO organisations (id, name, description, address, welcome_url, contact_url, logo_url, info)
                                 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                                 ON CONFLICT (id) DO NOTHING""",
                                 organisation['id'], organisation['name'],
                                 organisation.get('description', ''), organisation.get('address', ''),
                                 organisation.get('welcomeUrl', ''), organisation.get('contactUrl', ''),
                                 organisation.get('logoUrl', ''), json.dumps(organisation.get('info', '')))
        return True

    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to register organisation.')


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


async def db_register_service(connection, service):
    """Register new service at host."""
    LOG.debug('Register new service.')
    try:
        # Database commit occurs on transaction closure
        async with connection.transaction():
            # Create new organisation if one doesn't yet exist
            await db_register_organisation(connection, service['organization'])
            # Register service
            await connection.execute("""INSERT INTO services (id, name, service_type, api_version, service_url, host_org, description,
                                     service_version, open, welcome_url, alt_url, create_datetime, update_datetime)
                                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW(), NOW())""",
                                     service['id'], service['name'], service['serviceType'], service['apiVersion'], service['serviceUrl'],
                                     service['organization']['id'], service.get('description', ''), service.get('version', ''),
                                     service['open'], service.get('welcomeUrl', ''), service.get('alternativeUrl', ''))
            # If service registration was successful, generate and store a service key
            service_key = await generate_service_key()
            await db_store_service_key(connection, service['id'], service_key)
            return service_key  # return service key to registrar for later use

    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to register service.')


async def db_get_service_details(connection, id=None, service_type=None, api_version=None, list_format='full'):
    """Get all or selected service details."""
    LOG.debug('Get service details.')
    services = []

    # For handling prepared parameters
    sql_id = id if id is not None else True
    sql_service_type = service_type if service_type is not None else True
    sql_api_version = api_version if api_version is not None else True

    try:
        # Database query
        query = ''
        if list_format == 'short':
            # Minimal query
            query = f"""SELECT id AS ser_id, name AS ser_name, service_type AS ser_service_type,
                        service_url AS ser_service_url, open AS ser_open
                        FROM services
                        WHERE {'id=$1' if id is not None else '$1'}
                        AND {'service_type=$2' if service_type is not None else '$2'}
                        AND {'api_version=$3' if api_version is not None else '$3'}"""
        else:
            # Full query (default)
            query = f"""SELECT s.id AS ser_id, s.name AS ser_name, s.service_type AS ser_service_type, s.api_version AS ser_api_version,
                        s.service_url AS ser_service_url, s.host_org AS ser_host_org, s.description AS ser_description,
                        s.service_version AS ser_service_version, s.open AS ser_open,
                        s.welcome_url AS ser_welcome_url, s.alt_url AS ser_alt_url, s.create_datetime AS ser_createtime,
                        s.update_datetime AS ser_updatetime, o.id AS org_id, o.name AS org_name, o.description AS org_description,
                        o.address AS org_address, o.welcome_url AS org_welcome_url, o.contact_url AS org_contact_url,
                        o.logo_url AS org_logo_url, o.info AS org_info
                        FROM services s, organisations o
                        WHERE (s.host_org=o.id)
                        AND {'s.id=$1' if id is not None else '$1'}
                        AND {'s.service_type=$2' if service_type is not None else '$2'}
                        AND {'s.api_version=$3' if api_version is not None else '$3'}"""
        statement = await connection.prepare(query)
        response = await statement.fetch(sql_id, sql_service_type, sql_api_version)
        if len(response) > 0:
            for record in response:
                # Build JSON response
                service = await construct_json(record, list_format=list_format)
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


async def db_update_organisation(connection, service_id, org):
    """Update organisation."""
    LOG.debug('Update organisation.')

    # Check if user wants to change organisation id
    service_details = await db_get_service_details(connection, id=service_id)
    if not service_details['organization']['id'] == org['id']:
        # Unallowed operation
        raise web.HTTPBadRequest(text='Organisation ID can\'t be modified. Use POST to create a new organisation ID instead.')

    # Apply updates
    try:
        await connection.execute("""UPDATE organisations SET name=$1, description=$2, address=$3,
                                 welcome_url=$4, contact_url=$5, logo_url=$6, info=$7
                                 WHERE id=$8""",
                                 org.get('name'), org.get('description'), org.get('address'),
                                 org.get('welcomeUrl'), org.get('contactUrl'), org.get('logoUrl'),
                                 json.dumps(org.get('info')), org.get('id'))
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to update organisation details.')


async def db_update_service(connection, id, service):
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
        org_id = service['organization']['id']
        await connection.execute("""UPDATE services SET id=$1, name=$2, service_type=$3, api_version=$4,
                                 service_url=$5, host_org=$6, description=$7, service_version=$8,
                                 open=$9, welcome_url=$10, alt_url=$11, update_datetime=NOW()
                                 WHERE id=$12""",
                                 service.get('id'), service.get('name'), service.get('serviceType'),
                                 service.get('apiVersion'), service.get('serviceUrl'), org_id,
                                 service.get('description'), service.get('version'), service.get('open'),
                                 service.get('welcomeUrl'), service.get('alternativeUrl'), id)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to update service details.')


async def db_update_sequence(connection, id, updates):
    """Initiate update sequence."""
    LOG.debug('Initiate update sequence.')

    # Carry out operations within a transaction to avoid conflicts
    async with connection.transaction():
        # Update organisation first, because service has foreign key on organisation
        await db_update_organisation(connection, id, updates['organization'])
        await db_update_service(connection, id, updates)
        await db_update_service_key(connection, id, updates['id'])


async def db_verify_service_key(connection, service_id=None, service_key=None, alt_use_case=False):
    """Check if service id exists."""
    LOG.debug('Querying database to verify Beacon-Service-Key.')
    try:
        # Database query
        if service_id and not alt_use_case:
            # Use case for updating and deleting self at PUT|DELETE /services
            query = """SELECT service_id FROM service_keys WHERE service_id=$1 AND service_key=$2"""
            statement = await connection.prepare(query)
            response = await statement.fetch(service_id, service_key)
        else:
            # Use case for accessing remote Aggregator's PUT /beacons endpoint
            query = """SELECT remote_service FROM remote_keys WHERE service_key=$1"""
            statement = await connection.prepare(query)
            response = await statement.fetch(service_key)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify Beacon Service Key.')
    else:
        if len(response) == 0:
            LOG.debug('Provided service key is unauthorised.')
            raise web.HTTPUnauthorized(text='Unauthorised service key.')
        LOG.debug('Service key is authorised.')


async def db_verify_post_api_key(connection, api_key):
    """Check if provided api key for registration is authorised."""
    LOG.debug('Querying database to verify Post-Api-Key.')
    try:
        # Database query
        query = """SELECT comment FROM api_keys WHERE api_key=$1"""
        statement = await connection.prepare(query)
        response = await statement.fetch(api_key)
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to verify Post Api Key')
    else:
        if len(response) == 0:
            LOG.debug('Provided api key is unauthorised.')
            raise web.HTTPUnauthorized(text='Unauthorised api key.')
        LOG.debug('Api key is authorised.')
