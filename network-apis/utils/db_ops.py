"""Database Operations."""

import json

from aiohttp import web

from .logging import LOG

"""COMMON"""


async def db_check_service_id(connection, id):
    """Check if service id exists."""
    LOG.debug('Querying database for service id.')
    try:
        # Database query
        query = f"""SELECT name FROM services WHERE id='{id}'"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
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
        query = f"""SELECT name FROM organisations WHERE id='{id}'"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
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
        await connection.execute(f"""INSERT INTO organisations (id, name, description, address, welcome_url, contact_url, logo_url, info)
                                     VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                                     ON CONFLICT (id) DO NOTHING""",
                                     organisation['id'], organisation['name'],
                                     organisation.get('description'), organisation.get('address'),
                                     organisation.get('welcomeUrl'), organisation.get('contactUrl'),
                                     organisation.get('logoUrl'), json.dumps(organisation.get('info')))
        return True

    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to register organisation.')


async def db_register_service(connection, service):
    """Register new service at host."""
    LOG.debug('Register new service.')
    try:
        # Database commit occurs on transaction closure
        async with connection.transaction():
            # Create new organisation if one doesn't yet exist
            await db_register_organisation(connection, service['organization'])
            # Register service
            await connection.execute(f"""INSERT INTO services (id, name, service_type, api_version, service_url, host_org, description,
                                         service_version, public_key, open, welcome_url, alt_url, create_datetime, update_datetime)
                                         VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())""",
                                         service['id'], service['name'], service['serviceType'], service['apiVersion'], service['serviceUrl'],
                                         service['organization']['id'], service.get('description'), service.get('version'), service['publicKey'],
                                         service['open'], service.get('welcomeUrl'), service.get('alternativeUrl'))
            return True

    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to register service.')


async def construct_json(data, model=None, list_format='full'):
    """Construct proper JSON response from dictionary data."""
    LOG.debug('Construct JSON response from DB record.')
    # Minimal body when list_format='short'
    response = {
        "id": data.get('ser_id', ''),
        "name": data.get('ser_name', ''),
        "serviceType": data.get('ser_service_type', ''),
        "serviceUrl": data.get('ser_service_url', ''),
        "open": data.get('ser_open', '')
    }

    if list_format == 'full':
        # if list_format='full' or not specified -> defaults to full
        # update response to include all keys
        response.update(
            {
                "apiVersion": data.get('ser_api_version', ''),
                "organization": {
                    "id": data.get('org_id', ''),
                    "name": data.get('org_name', ''),
                    "description": data.get('org_description', ''),
                    "address": data.get('org_address', ''),
                    "welcomeUrl": data.get('org_welcome_url', ''),
                    "contactUrl": data.get('org_contact_url', ''),
                    "logoUrl": data.get('org_logo_url', ''),
                    "info": {}
                },
                "description": data.get('ser_description', ''),
                "version": data.get('ser_service_version', ''),
                "publicKey": data.get('ser_public_key', ''),
                "welcomeUrl": data.get('ser_welcome_url', ''),
                "alternativeUrl": data.get('ser_alt_url', ''),
                "createDateTime": str(data.get('ser_createtime', '')),
                "updateDateTime": str(data.get('ser_updatetime', ''))
            }
        )
        # Load the jsonb string into a dict and update the info-key
        response['organization']['info'].update(json.loads(data.get('org_info', '')))

    return response


async def db_get_service_details(connection, id=None, service_type=None, api_version=None, list_format='full'):
    """Get all or selected service details."""
    LOG.debug('Get service details.')
    services = []

    try:
        # Database query
        query = ''
        if list_format == 'short':
            # Minimal query
            query = f"""SELECT id AS ser_id, name AS ser_name, service_type AS ser_service_type,
                        service_url AS ser_service_url, open AS ser_open
                        FROM services
                        WHERE
                        {"id='" + id + "'" if id else 'TRUE'} AND
                        {"service_type='" + service_type + "'" if service_type else 'TRUE'} AND
                        {"api_version='" + api_version + "'" if api_version else 'TRUE'}"""
        else:
            # Full query (default)
            query = f"""SELECT s.id AS ser_id, s.name AS ser_name, s.service_type AS ser_service_type, s.api_version AS ser_api_version,
                        s.service_url AS ser_service_url, s.host_org AS ser_host_org, s.description AS ser_description,
                        s.service_version AS ser_service_version, s.public_key AS ser_public_key, s.open AS ser_open,
                        s.welcome_url AS ser_welcome_url, s.alt_url AS ser_alt_url, s.create_datetime AS ser_createtime,
                        s.update_datetime AS ser_updatetime, o.id AS org_id, o.name AS org_name, o.description AS org_description,
                        o.address AS org_address, o.welcome_url AS org_welcome_url, o.contact_url AS org_contact_url,
                        o.logo_url AS org_logo_url, o.info AS org_info
                        FROM services s, organisations o
                        WHERE
                        {"s.id='" + id + "'" if id else 'TRUE'} AND
                        {"s.service_type='" + service_type + "'" if service_type else 'TRUE'} AND
                        {"s.api_version='" + api_version + "'" if api_version else 'TRUE'} AND
                        s.host_org=o.id"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
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
        await connection.execute(f"""DELETE FROM services {"WHERE id='" + id + "'" if id else ''}""")
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
        await connection.execute(f"""UPDATE organisations SET name='{org.get('name')}',
                                     description='{org.get('description')}', address='{org.get('address')}',
                                     welcome_url='{org.get('welcomeUrl')}', contact_url='{org.get('contactUrl')}',
                                     logo_url='{org.get('logoUrl')}', info='{json.dumps(org.get('info'))}'
                                     WHERE id='{org.get('id')}'""")
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
        await connection.execute(f"""UPDATE services SET id='{service.get('id')}', name='{service.get('name')}',
                                     service_type='{service.get('serviceType')}', api_version='{service.get('apiVersion')}',
                                     service_url='{service.get('serviceUrl')}', host_org='{org_id}',
                                     description='{service.get('description')}', service_version='{service.get('version')}',
                                     public_key='{service.get('publicKey')}', open='{service.get('open')}',
                                     welcome_url='{service.get('welcomeUrl')}', alt_url='{service.get('alternativeUrl')}',
                                     update_datetime=NOW()
                                     WHERE id='{id}'""")
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


"""AGGREGATOR SPECIFIC"""


async def db_get_service_urls(connection):
    """Return queryable service urls."""
    LOG.debug('Querying database for service urls.')
    service_urls = []
    try:
        # Database query
        query = f"""SELECT service_url FROM services WHERE service_type='GA4GHBeacon' OR service_type='GA4GHBeaconAggregator'"""
        statement = await connection.prepare(query)
        response = await statement.fetch()
        if len(response) > 0:
            # Parse urls from psql records and append to list
            for record in response:
                service_urls.append(record['service_url'])
            return service_urls
        else:
            raise web.HTTPNotFound(text='No queryable services found.')
    except Exception as e:
        LOG.debug(f'DB error: {e}')
        raise web.HTTPInternalServerError(text='Database error occurred while attempting to fetch service urls.')


"""REGISTRY SPECIFIC"""

# Nothing
