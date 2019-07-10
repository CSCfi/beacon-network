"""Validation Utilities."""

from functools import wraps

from aiohttp import web
from jsonschema import Draft7Validator, validators
from jsonschema.exceptions import ValidationError

from .logging import LOG
from .db_ops import db_verify_api_key, db_verify_service_key


def extend_with_default(validator_class):
    """Include default values present in JSON Schema.
    Source: https://python-jsonschema.readthedocs.io/en/latest/faq/#why-doesn-t-my-schema-s-default-property-set-the-default-on-my-instance
    """
    validate_properties = validator_class.VALIDATORS["properties"]

    def set_defaults(validator, properties, instance, schema):
        for property, subschema in properties.items():
            if "default" in subschema:
                instance.setdefault(property, subschema["default"])

        for error in validate_properties(
            validator, properties, instance, schema,
        ):
            yield error

    return validators.extend(
        validator_class, {"properties": set_defaults},
    )


DefaultValidatingDraft7Validator = extend_with_default(Draft7Validator)


def validate(schema):
    """Validate JSON Schema, ensuring it is of correct form."""
    LOG.debug('Validate schema.')

    def wrapper(func):

        @wraps(func)
        async def wrapped(*args):
            request = args[-1]
            assert isinstance(request, web.Request)
            try:
                LOG.debug('Jsonify request body')
                request_body = await request.json()
            except Exception:
                LOG.debug('ERROR: Could not jsonify request body')
                raise web.HTTPBadRequest(text='Could not properly parse Request Body as JSON')
            try:
                LOG.debug('Validate against JSON schema')
                DefaultValidatingDraft7Validator(schema).validate(request_body)
            except ValidationError as e:
                LOG.debug(f'ERROR: Could not validate -> {request_body}, {request.host}, {e.message}')
                raise web.HTTPBadRequest(text=f'Could not validate request body: {e.message}')

            return await func(*args)
        return wrapped
    return wrapper


def api_key():
    """Check if API key is valid."""
    LOG.debug('Validate API key.')

    @web.middleware
    async def api_key_middleware(request, handler):
        LOG.debug('Start api key check')

        assert isinstance(request, web.Request)

        # Check which endpoint user is requesting and sort according to method
        if '/services' in request.path:
            LOG.debug('In /services endpoint.')
            if request.method == 'POST':
                LOG.debug('Using POST method.')
                try:
                    api_key = request.headers['Authorization']
                    LOG.debug('API key received.')
                except Exception:
                    LOG.debug('Missing "Authorization" from headers.')
                    raise web.HTTPBadRequest(text='Missing header "Authorization".')
                # Take one connection from the active database pool
                async with request.app['pool'].acquire() as connection:
                    # Check if provided api key is valid
                    await db_verify_api_key(connection, api_key)

                # None of the checks failed
                return await handler(request)

            # Handle other methods
            elif request.method in ['PUT', 'DELETE']:
                LOG.debug(f'Using {request.method} method.')
                if request.match_info.get('service_id'):
                    try:
                        beacon_service_key = request.headers['Beacon-Service-Key']
                        LOG.debug('Beacon-Service-Key received.')
                    except Exception:
                        LOG.debug('Missing "Beacon-Service-Key" from headers.')
                        raise web.HTTPBadRequest(text='Missing header "Beacon-Service-Key".')
                    # Take one connection from the active database pool
                    async with request.app['pool'].acquire() as connection:
                        # Verify that provided service key is authorised
                        await db_verify_service_key(connection, service_id=request.match_info.get('service_id'), service_key=beacon_service_key)
                else:
                    raise web.HTTPBadRequest(text='Missing path paremeter "/services/<service_id>".')
                # None of the checks failed
                return await handler(request)

            # Basically only GET /services goes here
            else:
                LOG.debug('No api key required at this endpoint.')
                return await handler(request)

        # For all other endpoints
        else:
            LOG.debug('No api key required at this endpoint.')
            return await handler(request)

    return api_key_middleware
