import asynctest

from aiohttp import web

from registry.utils.db_pool import init_db_pool
from registry.utils.db_ops import db_check_service_id, db_store_service_key, db_update_service_key
from registry.utils.db_ops import db_delete_service_key, db_register_service
from registry.utils.db_ops import db_get_service_details, db_delete_services, db_update_service
from registry.utils.db_ops import db_update_sequence, db_verify_service_key, db_verify_api_key, db_verify_admin_key

from .db_test_classes import Connection, BadConnection


class TestDatabase(asynctest.TestCase):
    """Test database setup."""

    @asynctest.mock.patch('registry.utils.db_pool.asyncpg')
    async def test_init_pool(self, db_mock):
        """Test database connection pool creation."""
        db_mock.return_value = asynctest.CoroutineMock(name='create_pool')
        db_mock.create_pool = asynctest.CoroutineMock()
        await init_db_pool(host='localhost', port='8080', user='user', passwd='pass', db='db')
        db_mock.create_pool.assert_called()


class TestDatabaseOperations(asynctest.TestCase):
    """Test database operations."""

    async def test_db_check_service_id_found(self):
        """Test service id checker: found."""
        connection = Connection(return_value=[{'name': 'Finnish Beacon'}])
        found = await db_check_service_id(connection, 'fi.beacon')
        self.assertTrue(found)

    async def test_db_check_service_id_none(self):
        """Test service id checker: not found."""
        connection = Connection(return_value=[])
        not_found = await db_check_service_id(connection, 'fi.beacon')
        self.assertFalse(not_found)

    async def test_db_check_service_id_error(self):
        """Test service id checker: error."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_check_service_id(connection, 'fi.beacon')

    async def test_db_store_service_key_success(self):
        """Test the storing of service key: successful storing."""
        connection = Connection()
        await db_store_service_key(connection, 'fi.beacon', 'abc123')
        # No exceptions raised

    async def test_db_store_service_key_fail(self):
        """Test the storing of service key: failed to store."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_store_service_key(connection, 'fi.beacon', 'abc123')

    async def test_db_update_service_key_success(self):
        """Test the updating of service key: successful update."""
        connection = Connection()
        await db_update_service_key(connection, 'fi.beacon', 'se.beacon')
        # No exceptions raised

    async def test_db_update_service_key_fail(self):
        """Test the updating of service key: failed to update."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_update_service_key(connection, 'fi.beacon', 'se.beacon')

    async def test_db_delete_service_key_success(self):
        """Test the deletion of service key: successful deletion."""
        connection = Connection()
        await db_delete_service_key(connection, 'fi.beacon')
        # No exceptions raised

    async def test_db_delete_service_key_fail(self):
        """Test the deletion of service key: failed to delete."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_delete_service_key(connection, 'fi.beacon')

    @asynctest.mock.patch('registry.utils.db_ops.db_store_service_key')
    @asynctest.mock.patch('registry.utils.db_ops.generate_service_key')
    async def test_db_register_service_success(self, mock_key, mock_store):
        """Test the registration of a new service: succesful registration."""
        mock_key.return_value = 'abc123'
        mock_store.return_value = True
        connection = Connection()
        service = {
            'id': 'id',
            'name': 'name',
            'type': 'type',
            'description': 'desc',
            'url': 'url',
            'contact_url': 'contact',
            'api_version': 'api',
            'service_version': 'version',
            'environment': 'env',
            'organization': 'org',
            'organization_url': 'url',
            'organization_logo': 'logo'
        }
        key = await db_register_service(connection, service)
        self.assertEqual(key, 'abc123')

    @asynctest.mock.patch('registry.utils.db_ops.db_store_service_key')
    @asynctest.mock.patch('registry.utils.db_ops.generate_service_key')
    async def test_db_register_service_fail(self, mock_key, mock_store):
        """Test the registration of a new service: failed to register."""
        mock_key.return_value = 'abc123'
        mock_store.return_value = True
        connection = Connection()
        service = {}  # Service data is missing keys, execute will fail
        with self.assertRaises(web.HTTPInternalServerError):
            await db_register_service(connection, service)

    @asynctest.mock.patch('registry.utils.db_ops.construct_json')
    async def test_db_get_service_details_found_by_id(self, mock_cons):
        """Test the retrieval of service details: successful retrieval of specifiec id."""
        connection = Connection(return_value=[{}])
        mock_cons.return_value = {}
        details = await db_get_service_details(connection, id='fi.beacon')
        # Requested specific service by id, so response is {}
        self.assertEqual(details, {})

    @asynctest.mock.patch('registry.utils.db_ops.construct_json')
    async def test_db_get_service_details_found_multiple(self, mock_cons):
        """Test the retrieval of service details: successful retrieval multiple services."""
        connection = Connection(return_value=[{}, {}, {}])
        mock_cons.return_value = {}
        details = await db_get_service_details(connection)
        # Requested all services, so response is [{}, ...]
        self.assertEqual(len(details), 3)

    async def test_db_get_service_details_none(self):
        """Test the retrieval of service details: none found."""
        connection = Connection()
        with self.assertRaises(web.HTTPNotFound):
            await db_get_service_details(connection, id='fi.beacon')

    async def test_db_get_service_details_fail(self):
        """Test the retrieval of service details: failed retrieval."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_get_service_details(connection, id='fi.beacon')

    @asynctest.mock.patch('registry.utils.db_ops.db_delete_service_key')
    async def test_db_delete_services_success(self, mock_del):
        """Test the deletion of a service: successful deletion."""
        mock_del.return_value = True
        connection = Connection()
        await db_delete_services(connection, 'fi.beacon')
        # No exceptions raised

    async def test_db_delete_services_fail(self):
        """Test the deletion of a service: failed to delete."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_delete_services(connection, 'fi.beacon')

    async def test_db_update_service_success(self):
        """Test the updating of a service: successful update."""
        connection = Connection()
        service_info = {
            'id': 'id',
            'name': 'name',
            'type': 'type',
            'description': 'desc',
            'url': 'url',
            'contact_url': 'contact',
            'api_version': 'api',
            'service_version': 'version',
            'environment': 'env',
            'organization': 'org',
            'organization_url': 'url',
            'organization_logo': 'logo'
        }
        await db_update_service(connection, 'id', service_info)
        # No exceptions raised

    @asynctest.mock.patch('registry.utils.db_ops.db_check_service_id')
    async def test_db_update_service_conflict(self, mock_id):
        """Test the updating of a service: service id taken."""
        mock_id.return_value = 'new.id'
        connection = Connection()
        with self.assertRaises(web.HTTPConflict):
            await db_update_service(connection, 'old.id', {'id': 'new.id'})

    async def test_db_update_service_fail(self):
        """Test the updating of a service: failed to update."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_update_service(connection, 'fi.beacon', {'id': 'fi.beacon'})

    @asynctest.mock.patch('registry.utils.db_ops.db_update_service_key')
    @asynctest.mock.patch('registry.utils.db_ops.db_update_service')
    async def test_db_update_sequence(self, mock_service, mock_key):
        """Test update sequence."""
        connection = Connection()
        mock_service.return_value = True
        mock_key.return_value = True
        await db_update_sequence(connection, 'fi.beacon', {'id': 'fi.beacon'})

    async def test_db_verify_service_key_success(self):
        """Test the verification of service key: successful verification."""
        connection = Connection(return_value=[{'service_id': 'fi.beacon'}])
        await db_verify_service_key(connection, 'fi.beacon', 'abc123')
        # No exceptions raised

    async def test_db_verify_service_key_fail(self):
        """Test the verification of service key: failed to verify."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_verify_service_key(connection, 'fi.beacon', 'abc123')

    async def test_db_verify_service_key_unauthorized(self):
        """Test the verification of service key: unauthorized key."""
        connection = Connection(return_value=[])
        with self.assertRaises(web.HTTPUnauthorized):
            await db_verify_service_key(connection, 'fi.beacon', 'abc123')

    async def test_db_verify_api_key_success(self):
        """Test the verification of api key: successful verification."""
        connection = Connection(return_value=[{'comment': 'dev'}])
        await db_verify_api_key(connection, 'abc123')
        # No exceptions raised

    async def test_db_verify_api_key_fail(self):
        """Test the verification of api key: failed to verify."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_verify_api_key(connection, 'abc123')

    async def test_db_verify_api_key_unauthorized(self):
        """Test the verification of api key: unauthorized key."""
        connection = Connection(return_value=[])
        with self.assertRaises(web.HTTPUnauthorized):
            await db_verify_api_key(connection, 'abc123')

    async def test_db_verify_admin_key_success(self):
        """Test the verification of admin key: successful verification."""
        connection = Connection(return_value=[{'comment': 'admin'}])
        await db_verify_admin_key(connection, 'abc123')
        # No exceptions raised

    async def test_db_verify_admin_key_fail(self):
        """Test the verification of admin key: failed to verify."""
        connection = BadConnection()
        with self.assertRaises(web.HTTPInternalServerError):
            await db_verify_admin_key(connection, 'abc123')

    async def test_db_verify_admin_key_unauthorized(self):
        """Test the verification of admin key: unauthorized key."""
        connection = Connection(return_value=[])
        with self.assertRaises(web.HTTPUnauthorized):
            await db_verify_admin_key(connection, 'abc123')


if __name__ == '__main__':
    asynctest.main()
