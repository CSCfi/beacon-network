import asynctest

from aioresponses import aioresponses
from aiohttp import web

from aggregator.utils.utils import http_get_service_urls, get_services, process_url
from aggregator.utils.utils import remove_self, get_access_token  # , query_service
from aggregator.utils.utils import validate_service_key  # , clear_cache


class MockRequest:
    """Mock request for testing."""

    def __init__(self, headers={}, cookies={}):
        """Initialise object."""
        self.headers = headers
        self.cookies = cookies


class MockWebsocket:
    """Mock Websocket for testing."""

    def __init__(self):
        """Initialise object."""
        self.data = None

    def send_str(self, data):
        """Receive data."""
        self.data = data


class TestUtils(asynctest.TestCase):
    """Test aggregator utility functions."""

    @aioresponses()
    async def test_http_get_service_urls_success(self, m):
        """Test successful request of service urls."""
        data = [
            {'type': 'org.ga4gh:beacon:1.0.0', 'url': 'https://beacon.fi/'},
            {'type': 'org.ga4gh:beacon-aggregator:1.0.0', 'url': 'https://beacon-aggregator.fi/'}
        ]
        m.get('https://beacon-registry.fi/services', status=200, payload=data)
        info = await http_get_service_urls('https://beacon-registry.fi/services')
        self.assertEqual(['https://beacon.fi/'], info)

    @aioresponses()
    async def test_http_get_service_urls_empty(self, m):
        """Test empty request of service urls."""
        data = []
        # If a server error occurred, and the response has no data, result should be an empty list
        m.get('https://beacon-registry.fi/services', status=400, payload=data)
        info = await http_get_service_urls('https://beacon-registry.fi/services')
        self.assertEqual([], info)

    # Looks like an exception can only occur if the aiohttp.ClientSession somehow fails
    # @aioresponses()
    # async def test_http_get_service_urls_fail(self, m):
    #     """Test failed request of service urls."""
    #     m.get('https://beacon-registry.fi/services', status=400)
    #     with self.assertRaises(aiohttp.web_exceptions.HTTPInternalServerError):
    #         await http_get_service_urls('https://beacon-registry.fi/services')

    @asynctest.mock.patch('aggregator.utils.utils.http_get_service_urls')
    @asynctest.mock.patch('aggregator.utils.utils.process_url')
    @asynctest.mock.patch('aggregator.utils.utils.remove_self')
    async def test_get_services(self, remo, proc, http):
        """Test retrieval of services."""
        http.return_value = ['https://beacon1.fi/', 'https://beacon2.fi/service-info', 'https://beacon-aggregator.fi/']
        proc.return_value = ['https://beacon1.fi/query', 'https://beacon2.fi/query', 'https://beacon-aggregator.fi/query']
        remo.return_value = ['https://beacon1.fi/query', 'https://beacon2.fi/query']
        services = await get_services('beacon-aggregator.fi')
        self.assertEqual(['https://beacon1.fi/query', 'https://beacon2.fi/query'], services)

    async def test_process_url_1(self):
        """Test url processing type 1."""
        processed = await process_url('https://beacon.fi/')
        self.assertEqual('https://beacon.fi/query', processed)

    async def test_process_url_2(self):
        """Test url processing type 2."""
        processed = await process_url('https://beacon.fi/service-info')
        self.assertEqual('https://beacon.fi/query', processed)

    async def test_process_url_3(self):
        """Test url processing type 3."""
        processed = await process_url('https://beacon.fi')
        self.assertEqual('https://beacon.fi/query', processed)

    async def test_remove_self(self):
        """Test removal of host from list of urls."""
        removed = await remove_self('https://thisisme.fi/', ['https://thisisyou.fi/', 'https://thisisme.fi/', 'https://thisisthem.fi/'])
        self.assertEqual(['https://thisisyou.fi/', 'https://thisisme.fi/', 'https://thisisthem.fi/'], removed)

    async def test_get_access_token_header_ok(self):
        """Test successful retrieval of access token from request headers."""
        request = MockRequest(headers={'Authorization': 'Bearer json.web.token'})
        access_token = await get_access_token(request)
        self.assertEqual('json.web.token', access_token)

    async def test_get_access_token_header_wrong_scheme(self):
        """Test successful retrieval of access token from request headers."""
        request = MockRequest(headers={'Authorization': 'Basic json.web.token'})
        with self.assertRaises(web.HTTPBadRequest):
            await get_access_token(request)

    async def test_get_access_token_header_error(self):
        """Test errored retrieval of access token from request headers."""
        request = MockRequest(headers={'Authorization': 'json.web.token'})
        with self.assertRaises(web.HTTPBadRequest):
            await get_access_token(request)

    async def test_get_access_token_cookie(self):
        """Test retrieval of access token from request."""
        request = MockRequest(cookies={'access_token': 'json.web.token'})
        access_token = await get_access_token(request)
        self.assertEqual('json.web.token', access_token)

    async def test_get_access_token_none(self):
        """Test retrieval of access token from request."""
        request = MockRequest()
        access_token = await get_access_token(request)
        self.assertEqual(None, access_token)

    # find out why query_service returns None

    # @aioresponses()
    # async def test_query_service_ws_success(self, m):
    #     """Test querying of service: websocket success."""
    #     data = {'important': 'stuff'}
    #     m.get('https://beacon.fi/query', status=200, payload=data)
    #     ws = MockWebsocket()
    #     await query_service('https://beacon.fi/query', 'referenceName=1', 'json.web.token', ws=ws)
    #     self.assertEqual(ws.data, data)

    # async def test_query_service_ws_fail(self):
    #     """Test querying of service: websocket fail."""

    # @aioresponses()
    # async def test_query_service_http_success(self, m):
    #     """Test querying of service: http success."""
    #     data = {'important': 'stuff'}
    #     m.get('https://beacon.fi/query', status=200, payload=data)
    #     response = await query_service('https://beacon.fi/query', 'referenceName=1', 'json.web.token')
    #     self.assertEqual(response, data)

    # async def test_query_service_http_fail(self):
    #     """Test querying of service: http fail."""

    # async def test_query_service_error(self):
    #     """Test querying of service: general fail."""

    async def test_validate_service_key_success(self):
        """Successfully validate service key."""
        validated = await validate_service_key('secret')
        self.assertTrue(validated)

    async def test_validate_service_key_fail(self):
        """Successfully validate service key."""
        with self.assertRaises(web.HTTPUnauthorized):
            await validate_service_key('wrong key')


if __name__ == '__main__':
    asynctest.main()
