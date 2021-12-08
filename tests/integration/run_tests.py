"""Run integration tests against backend api endpoints."""
import asyncio
import httpx
import logging
import re
import ujson

FORMAT = "[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s](L:%(lineno)s) %(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

AGGREGATOR = "http://localhost:5054"
REGISTRY = "http://localhost:8083"
REGISTRY_KEY = "07b4e8ed58a6f97897b03843474c8cc981d154ffe45b10ef88a9f127b15c5c56"


async def test_service_info(endpoint, name, artifact):
    """Test service info endpoint."""
    LOG.debug(f"Checking service info endpoint for: {artifact}")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{endpoint}/service-info")
        assert response.status_code == 200, "HTTP status code error service info"
        data = response.json()
        assert data["name"] == name, "Wrong endpoint service name"
        assert data["type"]["artifact"] == artifact, "Wrong service artifact"


async def test_get_services(endpoint, expected_nb, expected_beacon, version):
    """Test GET services registry."""
    LOG.debug("Checking registry listing services")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{endpoint}/services")
        assert response.status_code == 200, "HTTP status code error service info"
        data = response.json()
        assert len(data) == expected_nb, "We did not find the expected number of services"
        if version == 1:

            assert re.search(f'"id":"{expected_beacon}"', ujson.dumps(data, escape_forward_slashes=False), re.M), "We did not find the expected beacon"

        # we don't fail this test as running on localhost this might be problematic
        if version == 2:
            beacon2 = re.search(f'"id":"{expected_beacon}"', ujson.dumps(data, escape_forward_slashes=False), re.M)
            if beacon2:
                data = next((x for x in data if x.get("id") == expected_beacon), None)
                if data["type"]["version"] not in ["2.0.0"]:
                    print("We did not find the expected 2.0. beacon")

    LOG.debug("Checking registry listing services types")
    async with httpx.AsyncClient() as client:
        server_types = await client.get(f"{endpoint}/services/types")
        data = server_types.json()
        assert data == [
            "service-registry",
            "beacon-aggregator",
            "beacon",
        ], "We did not find the expected services types"


async def test_service_operations(endpoint):
    """Test Registry services operations."""
    extra_beacon = {"type": "beacon", "url": "http://extra_bad_beacon:5053/service-info"}
    update_beacon = {"type": "beacon", "url": "http://bad_beacon:5052/service-info"}

    LOG.debug("Add new service to the registry")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{endpoint}/services",
            data=ujson.dumps(extra_beacon, escape_forward_slashes=False),
            headers={"Authorization": REGISTRY_KEY},
        )
        assert response.status_code == 201, "HTTP status code error service add"
        data = response.json()
        assert data["serviceId"] == "extra_bad_beacon:5053", "Wrong beacon id obtained"

    LOG.debug("Update service from the registry with existing one")
    async with httpx.AsyncClient() as client:
        conflict_response = await client.put(
            f"{endpoint}/services/{data['serviceId']}",
            data=ujson.dumps(update_beacon, escape_forward_slashes=False),
            headers={"Beacon-Service-Key": data["serviceKey"]},
        )

        conflict_data = conflict_response.json()
        assert conflict_response.status_code == 409, "HTTP status code error service update"
        assert conflict_data["error"] == "Another service has already been registered with the new service id.", "Conflict error mismatched"

    LOG.debug("Update service from the registry correctly")
    async with httpx.AsyncClient() as client:
        update_response = await client.put(
            f"{endpoint}/services/{data['serviceId']}",
            data=ujson.dumps(extra_beacon, escape_forward_slashes=False),
            headers={"Beacon-Service-Key": data["serviceKey"]},
        )

        updated_data = update_response.json()
        assert update_response.status_code == 200, "HTTP status code error service update"

    LOG.debug("Remove service from the registry")
    async with httpx.AsyncClient() as client:
        await client.delete(f"{endpoint}/services/{updated_data['newServiceId']}", headers={"Beacon-Service-Key": data["serviceKey"]})
        assert update_response.status_code == 200, "HTTP status code error service delete"


async def test_query_aggregator(endpoint, expected_beacon):
    """Test Aggregator query operation."""
    LOG.debug("make a query over the aggregator")
    params = {
        "includeDatasetResponses": "HIT",
        "assemblyId": "GRCh38",
        "referenceName": "MT",
        "start": "9",
        "referenceBases": "T",
        "alternateBases": "C",
    }
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{endpoint}/query", params=params)
        data = response.json()
        assert response.status_code == 200, "HTTP status code error aggregator query"
        assert re.search(f'"service":"{expected_beacon}"', ujson.dumps(data, escape_forward_slashes=False), re.M), "We did not find the expected beacon"


async def main():
    """Launch different test tasks and run them."""
    LOG.debug("=== Test Service Info ===")

    await test_service_info(AGGREGATOR, "ELIXIR-FI Beacon Aggregator", "beacon-aggregator")
    await test_service_info(REGISTRY, "ELIXIR-FI Beacon Registry", "service-registry")

    LOG.debug("=== Test Registry Endpoint ===")

    await test_get_services(REGISTRY, 5, "bad_beacon:5052", 1)
    await test_get_services(REGISTRY, 5, "beacon:5050", 2)
    await test_service_operations(REGISTRY)

    LOG.debug("=== Test Aggregator Endpoint ===")
    await test_query_aggregator(AGGREGATOR, "http://bad_beacon:5052/query")


if __name__ == "__main__":
    asyncio.run(main())
