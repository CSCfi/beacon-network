"""Run integration tests against backend api endpoints."""
import asyncio
import httpx
import logging

FORMAT = "[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s](L:%(lineno)s) %(funcName)s: %(message)s"
logging.basicConfig(format=FORMAT, datefmt="%Y-%m-%d %H:%M:%S")
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)

SESSION = httpx.AsyncClient()

AGGREGATOR = "http://localhost:5050"
REGISTRY = "http://localhost:8080"


async def test_service_info(endpoint, name, artifact):
    """Test service info endpoint."""
    LOG.debug(f"Checking service info endpoint for: {artifact}")
    response = await SESSION.get(f"{endpoint}/service-info")
    assert response.status_code == 200, "HTTP status code error service info"
    data = response.json()
    assert data["name"] == name, "Wrong endpoint service name"
    assert data["type"]["artifact"] == artifact, "Wrong service artifact"


async def main():
    """Launch different test tasks and run them."""
    LOG.debug("=== Test Service Info ===")

    await test_service_info(AGGREGATOR, "ELIXIR-FI Beacon Aggregator", "beacon-aggregator")
    await test_service_info(REGISTRY, "ELIXIR-FI Beacon Registry", "service-registry")

    await SESSION.aclose()


if __name__ == "__main__":
    asyncio.run(main())
