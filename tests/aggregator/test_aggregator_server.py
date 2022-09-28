import unittest
import asynctest

from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from aggregator.aggregator import init_app


class AppTestCase(AioHTTPTestCase):
    """Test aggregator endpoints."""

    async def get_application(self):
        """Retrieve web application for test."""
        return await init_app()

    @unittest_run_loop
    async def test_response_headers(self):
        """Test response headers are set correctly in on_prepare_response."""
        resp = await self.client.request("GET", "/")
        assert 200 == resp.status
        assert "Beacon-Network" == resp.headers.get("Server", "")

    @unittest_run_loop
    async def test_index(self):
        """Test root endpoint."""
        resp = await self.client.request("GET", "/")
        assert 200 == resp.status
        assert "ELIXIR-FI Beacon Test" == await resp.text()

    @unittest_run_loop
    async def test_service_info(self):
        """Test service info endpoint."""
        resp = await self.client.request("GET", "/service-info")
        data = await resp.json()
        assert 200 == resp.status
        assert "ELIXIR-FI Beacon Test" == data["name"]
        assert data["type"]["artifact"] == "beacon-test"

    @unittest_run_loop
    async def test_delete_cache(self):
        """Test cache deletion endpoint."""
        resp = await self.client.request("DELETE", "/cache", headers={"Authorization": "secret"})
        assert 200 == resp.status
        assert "Cache has been deleted." == await resp.text()

    @asynctest.mock.patch("aggregator.aggregator.send_beacon_query")
    @unittest_run_loop
    async def test_query_normal(self, m_query):
        """Test query endpoint, normal query."""
        m_query.return_value = ["normal query"]
        resp = await self.client.request("GET", "/query")
        data = await resp.json()
        assert 200 == resp.status
        assert data == ["normal query"]

    # Doesn't go to the websocket block at all even with the headers
    # fails with 'aiohttp.client_exceptions.ServerDisconnectedError'
    # @asynctest.mock.patch('aggregator.aggregator.send_beacon_query_websocket')
    # @unittest_run_loop
    # async def test_query_websocket(self, m_query_ws):
    #     """Test query endpoint, websocket query."""
    #     # Test that when using websocket headers, the query is handled by the websocket handler
    #     m_query_ws.return_value = 'websocket query'
    #     #resp = await self.client.request("GET", "/query", headers={"Connection": "Upgrade", "Upgrade": "Websocket"})
    #     resp = await self.client.request("GET", "/query", headers={"Connection": "Upgrade", "Upgrade": "Websocket", "Connection": "Close"})
    #     # data = await resp.json()  # response is something else than this
    #     assert 200 == resp.status
    #     # assert data == 'websocket query'


if __name__ == "__main__":
    unittest.main()
