import unittest

import asyncpg
import asynctest

from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from registry.registry import main, init_app


async def create_db_mock(app):
    """Mock the db connection pool."""
    app['pool'] = asynctest.mock.Mock(asyncpg.create_pool())
    return app


class TestRegistryEndpoints(AioHTTPTestCase):
    """Test registry endpoints."""

    @asynctest.mock.patch('registry.registry.init_db', side_effect=create_db_mock)
    async def get_application(self, mock_db):
        """Retrieve web application for test."""
        return await init_app()

    @unittest_run_loop
    async def test_index(self):
        """Test root endpoint."""
        resp = await self.client.request("GET", "/")
        assert 200 == resp.status
        assert 'ELIXIR-FI Beacon Registry' == await resp.text()

    @unittest_run_loop
    async def test_service_info(self):
        """Test service info endpoint."""
        resp = await self.client.request("GET", "/service-info")
        data = await resp.json()
        assert 200 == resp.status
        assert 'ELIXIR-FI Beacon Registry' == data['name']
        assert data['type']['artifact'] == 'service-registry'

    @unittest_run_loop
    async def test_service_types(self):
        """Test service types endpoint."""
        resp = await self.client.request("GET", "/services/types")
        data = await resp.json()
        assert 200 == resp.status
        assert 'service-registry' == data[0]
        assert 'beacon-aggregator' == data[1]
        assert 'beacon' == data[2]

    # @asynctest.mock.patch('registry.registry.invalidate_aggregator_caches')
    # @asynctest.mock.patch('registry.registry.register_service')
    # @unittest_run_loop
    # async def test_post_services(self, mock_post, mock_cache):
    #     """Test services endpoint: register a new service."""
    #     post_data = {
    #         'email': 'admin@beacon.fi',
    #         'type': 'org.ga4gh:beacon',
    #         'url': 'https://beacon.fi/service-info'
    #     }
    #     mock_post.return_value = {'message': 'Service has been registered.',
    #                               'serviceId': 'fi.beacon',
    #                               'serviceKey': 'abc123',
    #                               'help': 'docs'}
    #     mock_cache.return_value = True
    #     resp = await self.client.request("GET", "/services", data=json.dumps(post_data))
    #     # data = await resp.json()
    #     assert 201 == resp.status
    #     # assert 'Service has been registered.' == data['message']
    #     # assert 'fi.beacon' == data['serviceId']

    @asynctest.mock.patch('registry.registry.get_services')
    @unittest_run_loop
    async def test_get_services(self, mock_get):
        """Test services endpoint: get list of services."""
        mock_get.return_value = {'id': 'fi.beacon'}
        resp = await self.client.request("GET", "/services")
        data = await resp.json()
        assert 200 == resp.status
        assert 'fi.beacon' == data['id']

    @asynctest.mock.patch('registry.registry.get_services')
    @unittest_run_loop
    async def test_get_service_id(self, mock_get):
        """Test services endpoint: get service by id."""
        mock_get.return_value = {'id': 'fi.beacon'}
        resp = await self.client.request("GET", "/services/fi.beacon")
        data = await resp.json()
        assert 200 == resp.status
        assert 'fi.beacon' == data['id']


class TestRegistryStartUp(asynctest.TestCase):
    """Test registry start up functions."""

    def setUp(self):
        """Initialise fixtures."""
        pass

    def tearDown(self):
        """Remove setup variables."""
        pass

    @asynctest.mock.patch('registry.registry.web')
    def test_main(self, mock_web):
        """Test starting of web app."""
        main()
        mock_web.run_app.assert_called()

    async def test_init(self):
        """Test init type."""
        server = await init_app()
        self.assertIs(type(server), web.Application)


if __name__ == '__main__':
    unittest.main()
