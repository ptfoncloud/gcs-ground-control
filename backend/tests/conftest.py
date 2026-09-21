import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.vehicle import VehicleManager
from app.schemas import TelemetryFrame

@pytest.fixture
def fresh_vehicle():
    "Provides an isolated VehicleManager instance initialized to nominal ground state."
    vm = VehicleManager()
    vm.latest_telemetry = TelemetryFrame(
        timestamp=1000.0,
        armed=False,
        flight_mode="MANUAL",
        altitude=0.0,
        ground_speed=0.0,
        battery_voltage=12.6,
        pitch=0.0,
        roll=0.0,
        yaw=0.0,
        packets_rx=0,
        packet_loss_pct=0.0,
        lat=35.0594,
        lon=-118.1517
    )
    vm.last_seq = None
    vm.packets_lost = 0
    vm.packets_rx = 0
    return vm

@pytest_asyncio.fixture
async def async_client():
    "Asynchronous client for testing FastAPI command endpoints."
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client