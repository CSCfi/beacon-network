import asynctest
import aiohttp

from registry.endpoints.update import update_service_infos, update_sequence
from registry.endpoints.services import register_service, update_service
from registry.endpoints.services import get_services, delete_services


class MockRequest:
    """Mock request for testing."""

    def __init__(self, json_to_dict={}):
        """Initialise object."""
        self.json_to_dict = json_to_dict
        self.headers = {"Authorization": "secret"}

    async def json(self):
        """Return json contents in dict form."""
        return self.json_to_dict


class TestUtils(asynctest.TestCase):
    """Test registry endpoint processors."""

    @asynctest.mock.patch("registry.endpoints.services.db_update_sequence")
    @asynctest.mock.patch("registry.endpoints.services.parse_service_info")
    @asynctest.mock.patch("registry.endpoints.services.http_request_info")
    @asynctest.mock.patch("registry.endpoints.services.generate_service_id")
    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_update_service_success(self, m_params, db_check, m_generate, m_http, m_parse, m_update):
        """Test updating of service info: successfully updated."""
        m_request = MockRequest(json_to_dict={"url": "https://beacon.csc.fi/"})
        m_params.return_value = "fi.csc.beacon2000", None
        db_check.return_value = True
        m_generate.return_value = "fi.csc.beacon2000"
        m_http.return_value = {}
        m_parse.return_value = {}
        m_update.return_value = True
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        response = await update_service(m_request, m_pool)
        self.assertTrue(response["message"].startswith("Service has been updated."))

    @asynctest.mock.patch("registry.endpoints.services.generate_service_id")
    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_update_service_id_taken(self, m_params, db_check, m_generate):
        """Test updating of service info: new id is taken."""
        m_request = MockRequest(json_to_dict={"url": "https://beacon.csc.fi/"})
        m_params.return_value = "fi.csc.beacon2000", None
        db_check.return_value = True
        m_generate.return_value = "fi.csc.beacon"
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        with self.assertRaises(aiohttp.web.HTTPConflict):
            await update_service(m_request, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_update_service_not_found(self, m_params, db_check):
        """Test updating of service info: service not found."""
        m_request = MockRequest(json_to_dict={"url": "https://beacon.csc.fi/"})
        m_params.return_value = "fi.csc.beacon2000", None
        db_check.return_value = False
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        with self.assertRaises(aiohttp.web.HTTPNotFound):
            await update_service(m_request, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_update_service_fail(self, m_params):
        """Test updating of service info: missing service id."""
        m_request = MockRequest(json_to_dict={"url": "https://beacon.csc.fi/"})
        m_params.return_value = "", None
        m_pool = asynctest.CoroutineMock()
        with self.assertRaises(aiohttp.web.HTTPBadRequest):
            await update_service(m_request, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.generate_service_id")
    @asynctest.mock.patch("registry.endpoints.services.http_request_info")
    async def test_register_service_beacon_id_taken(self, m_http, m_generate, m_check):
        """Test service registration: beacon, id taken."""
        m_request = MockRequest()
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        m_http.return_value = {}  # service info
        m_generate.return_value = "fi.csc.beacon"  # generated id
        m_check.return_value = True
        with self.assertRaises(aiohttp.web.HTTPConflict):
            await register_service(m_request, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.db_delete_api_key")
    @asynctest.mock.patch("registry.endpoints.services.db_register_service")
    @asynctest.mock.patch("registry.endpoints.services.parse_service_info")
    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.generate_service_id")
    @asynctest.mock.patch("registry.endpoints.services.http_request_info")
    async def test_register_service_beacon_success(self, m_http, m_generate, m_check, m_parse, m_register, m_apikey):
        """Test service registration: beacon, success."""
        m_request = MockRequest(json_to_dict={"type": "beacon"})
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        m_http.return_value = {}  # service info
        m_generate.return_value = "fi.csc.beacon"  # generated id
        m_check.return_value = False
        m_parse.return_value = {}
        m_register.return_value = "key"
        m_apikey.return_value = True
        response = await register_service(m_request, m_pool)
        self.assertEqual(response["serviceKey"], "key")
        self.assertEqual(response["serviceId"], "fi.csc.beacon")
        self.assertEqual(
            response["message"],
            "Service has been registered. Service key and id for updating and deleting " "registration included in this response, keep them safe.",
        )

    @asynctest.mock.patch("registry.endpoints.services.db_delete_api_key")
    @asynctest.mock.patch("registry.endpoints.services.db_register_service")
    @asynctest.mock.patch("registry.endpoints.services.parse_service_info")
    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.generate_service_id")
    @asynctest.mock.patch("registry.endpoints.services.http_request_info")
    async def test_register_service_aggregator_success(self, m_http, m_generate, m_check, m_parse, m_register, m_apikey):
        """Test service registration: aggregator, success."""
        m_request = MockRequest(json_to_dict={"type": "beacon-aggregator"})
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        m_http.return_value = {}  # service info
        m_generate.return_value = "fi.csc.aggregator"  # generated id
        m_check.return_value = False
        m_parse.return_value = {}
        m_register.return_value = "key"
        m_apikey.return_value = True
        response = await register_service(m_request, m_pool)
        self.assertEqual(response["serviceKey"], "key")
        self.assertEqual(response["serviceId"], "fi.csc.aggregator")
        self.assertEqual(
            response["message"],
            "Service has been registered. Service key and id for updating and deleting "
            "registration included in this response, keep them safe. Add this key to "
            "`registries.json` to allow this Registry to invalidate the cached Beacons "
            "at your Aggregator in case of catalogue changes.",
        )

    @asynctest.mock.patch("registry.endpoints.update.update_sequence")
    @asynctest.mock.patch("registry.endpoints.update.db_get_service_details")
    async def test_update_service_infos(self, m_db, m_update):
        """Test updating of service infos."""
        m_db.return_value = ["https://aggregator.csc.fi/service-info"]
        m_update.return_value = None
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        fails, total = await update_service_infos({}, m_pool)
        self.assertEqual(0, fails)
        self.assertEqual(1, total)

    @asynctest.mock.patch("registry.endpoints.update.db_update_service")
    @asynctest.mock.patch("registry.endpoints.update.parse_service_info")
    @asynctest.mock.patch("registry.endpoints.update.http_request_info")
    async def test_update_service_info_success(self, m_http, m_parse, m_db):
        """Test updating of service info: successful update."""
        service = {"id": "fi.csc.aggregator", "url": "https://aggregator.csc.fi"}
        m_http.return_value = service
        m_parse.return_value = service
        m_db.return_value = True
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        await update_sequence(service, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.db_get_service_details")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_get_services(self, m_params, m_db):
        """Test retrieval of services."""
        m_params.return_value = "fi.csc.aggregator", {}
        m_db.return_value = {"id": "fi.csc.aggregator"}
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        response = await get_services({}, m_pool)
        self.assertEqual(response, {"id": "fi.csc.aggregator"})

    @asynctest.mock.patch("registry.endpoints.services.db_delete_services")
    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_delete_services_success(self, m_params, m_check, m_delete):
        """Test retrieval of services: successful deletion."""
        m_params.return_value = "fi.csc.aggregator", {}
        m_check.return_value = True
        m_delete.return_value = True
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        await delete_services({}, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.db_check_service_id")
    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_delete_services_fail(self, m_params, m_check):
        """Test retrieval of services: failed to delete."""
        m_params.return_value = "fi.csc.aggregator", {}
        m_check.return_value = False
        m_pool = asynctest.CoroutineMock()
        m_pool.acquire().__aenter__.return_value = True
        with self.assertRaises(aiohttp.web.HTTPNotFound):
            await delete_services({}, m_pool)

    @asynctest.mock.patch("registry.endpoints.services.query_params")
    async def test_delete_services_forbidden(self, m_params):
        """Test retrieval of services: forbidden mass deletion."""
        m_params.return_value = None, {}
        m_pool = asynctest.CoroutineMock()
        with self.assertRaises(aiohttp.web.HTTPForbidden):
            await delete_services({}, m_pool)


if __name__ == "__main__":
    asynctest.main()
