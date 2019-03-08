"""Validation Utilities."""

from functools import wraps

from aiohttp import web
from jsonschema import Draft7Validator, validators
from jsonschema.exceptions import ValidationError

from .logging import LOG


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
        if '/services' in request.path and request.method == 'POST' and 'Post-Api-Key' in request.headers:
            LOG.debug('In /services path using POST with api key.')
            try:
                post_api_key = request.headers.get('Post-Api-Key')
                LOG.debug('API key received.')
            except Exception as e:  # KeyError
                LOG.error(f'ERROR: Something wrong with fetching api key from headers: {e}')
                raise web.HTTPBadRequest(text=f'Missing header: {e}')

            if post_api_key is not None:
                # Take one connection from the active database connection pool
                async with request.app['pool'].acquire() as connection:
                    # Check if api key exists in database
                    query = f"""SELECT comment FROM api_keys WHERE api_key=$1"""
                    statement = await connection.prepare(query)
                    db_response = await statement.fetch(post_api_key)
                    if not db_response:
                        LOG.error(f'Provided API key is Unauthorized.')
                        raise web.HTTPUnauthorized(text='Unauthorized api key')
                    LOG.debug('Provided api key is authorized')
            # Carry on with user request
            return await handler(request)
        elif '/services' not in request.path or request.method != 'POST':
            LOG.debug('No api key required at this endpoint.')
            return await handler(request)
        else:
            LOG.error('Missing api key header.')
            raise web.HTTPBadRequest(text="Missing header: 'Post-Api-Key'")
    return api_key_middleware
