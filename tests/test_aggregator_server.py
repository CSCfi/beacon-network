import unittest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from aggregator.aggregator import init_app


class AppTestCase(AioHTTPTestCase):
    """Test endpoints."""

    async def get_application(self):
        """Retrieve web application for test."""
        return await init_app()

    @unittest_run_loop
    async def test_index(self):
        """Test root endpoint."""
        resp = await self.client.request("GET", "/")
        assert 200 == resp.status
        assert 'ELIXIR-FI Beacon Aggregator' == await resp.text()

    @unittest_run_loop
    async def test_service_info(self):
        """Test service info endpoint."""
        resp = await self.client.request("GET", "/service-info")
        data = await resp.json()
        assert 200 == resp.status
        assert 'ELIXIR-FI Beacon Aggregator' == data['name']
        assert data['type'].startswith('org.ga4gh:beacon-aggregator')


if __name__ == '__main__':
    unittest.main()
