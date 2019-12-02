import asynctest

from aiohttp.test_utils import unittest_run_loop

from aggregator.endpoints.cache import invalidate_cache
from aggregator.endpoints.info import get_info
from aggregator.endpoints.query import send_beacon_query, send_beacon_query_websocket


class MockWebsocket:
    """Mock websocket for testing."""

    def __init__(self):
        """Initialise object."""
        self.request = None

    async def prepare(self, request):
        """Prepare websocket."""
        self.request = request
        return True

    async def close(self):
        """Close websocket."""
        return True


class MockRequest:
    """Mock request for testing."""

    def __init__(self, query_string='', host=''):
        """Initialise object."""
        self.query_string = query_string
        self.host = host
        self._loop = True


class TestUtils(asynctest.TestCase):
    """Test aggregator endpoint processors."""

    @asynctest.mock.patch('aggregator.endpoints.cache.LOG')
    async def test_invalidate_cache(self, m_log):
        """Test cache invalidation request."""
        await invalidate_cache()
        m_log.debug.assert_called_with('Cache invalidating procedure complete.')

    async def test_get_info(self):
        """Test info request."""
        generated_info = await get_info('beacon.csc.fi')
        self.assertEqual(generated_info['id'], 'fi.csc.beacon')

    @asynctest.mock.patch('aggregator.endpoints.query.query_service')
    @asynctest.mock.patch('aggregator.endpoints.query.get_access_token')
    @asynctest.mock.patch('aggregator.endpoints.query.get_services')
    async def test_send_beacon_query(self, m_services, m_token, m_query):
        """Test normal beacon query (sync. http)."""
        m_request = MockRequest(host='aggregator.csc.fi')
        m_services.return_value = ['https://beacon1.csc.fi/query', 'https://beacon2.csc.fi/query']
        m_token.return_value = 'token'
        m_query.return_value = {'exists': True}
        query_results = await send_beacon_query(m_request)
        self.assertEqual(query_results, [{'exists': True}, {'exists': True}])

    @asynctest.mock.patch('aggregator.endpoints.query.web.WebSocketResponse')
    @asynctest.mock.patch('aggregator.endpoints.query.query_service')
    @asynctest.mock.patch('aggregator.endpoints.query.get_access_token')
    @asynctest.mock.patch('aggregator.endpoints.query.get_services')
    @unittest_run_loop
    async def test_send_beacon_query_websocket(self, m_services, m_token, m_query, m_ws):
        """Test websocket beacon query (async. ws)."""
        m_ws.return_value = MockWebsocket()
        m_request = MockRequest(host='aggregator.csc.fi')
        m_services.return_value = ['https://beacon1.csc.fi/query', 'https://beacon2.csc.fi/query']
        m_token.return_value = 'token'
        m_query.return_value = {'exists': True}
        websocket = await send_beacon_query_websocket(m_request)
        # Test that the function returns a websocket response
        self.assertTrue(isinstance(websocket, MockWebsocket))


if __name__ == '__main__':
    asynctest.main()
