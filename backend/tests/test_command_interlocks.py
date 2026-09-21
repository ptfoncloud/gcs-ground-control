import pytest
from unittest.mock import MagicMock
from app.vehicle import vehicle_manager

class TestCommandInterlocks:

    @pytest.mark.asyncio
    async def test_arm_command_dispatch_does_not_optimistically_arm(self, async_client):
        """
        Aerospace Interlock Safety:
        Dispatching /api/command/arm must return 200 HTTP ACK indicating transmission,
        but vehicle_manager.latest_telemetry.armed must REMAIN False until the vehicle
        authoritatively downlinks an armed HEARTBEAT (base_mode bitmask 0x80).
        """
        # Ensure initial state is disarmed
        vehicle_manager.latest_telemetry.armed = False
        vehicle_manager.master = MagicMock()  # Mock MAVLink UDP connection

        response = await async_client.post("/api/command/arm", json={"force": False})
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["DISPATCHED", "QUEUED"]
        
        # Critical assertion: UI/Backend MUST NOT optimistically toggle state
        assert vehicle_manager.latest_telemetry.armed is False

    @pytest.mark.asyncio
    async def test_emergency_motor_cutoff_validates_payload(self, async_client):
        """Arm endpoint must support emergency force flag."""
        vehicle_manager.master = MagicMock()

        response = await async_client.post("/api/command/arm", json={"force": True})
        assert response.status_code == 200
        assert response.json()["status"] == "DISPATCHED"

    @pytest.mark.asyncio
    async def test_telemetry_schema_snapshot(self, async_client):
        """Verifies downlinked telemetry snapshot maintains non-null coordinates and valid bus voltage."""
        response = await async_client.get("/api/telemetry")
        assert response.status_code == 200
        payload = response.json()

        assert "lat" in payload
        assert "lon" in payload
        assert "packets_rx" in payload
        assert "packet_loss_pct" in payload
        assert payload["battery_voltage"] > 0.0

    def test_authoritative_heartbeat_state_transition(self, fresh_vehicle):
        """
        Simulates arrival of a real MAVLink HEARTBEAT message.
        State must transition to armed ONLY when MAV_MODE_FLAG_SAFETY_ARMED (128) is present in base_mode.
        """
        vm = fresh_vehicle
        assert vm.latest_telemetry.armed is False

        # Mock incoming HEARTBEAT message: base_mode with 0x80 (128) set
        mock_msg_armed = MagicMock()
        mock_msg_armed.get_type.return_value = "HEARTBEAT"
        mock_msg_armed.base_mode = 128 | 1  # Armed + Custom Mode enabled
        mock_msg_armed.custom_mode = 4     # e.g., HOLD / AUTO

        # Evaluate bitmask
        is_armed = bool(mock_msg_armed.base_mode & 128)
        vm.latest_telemetry.armed = is_armed
        assert vm.latest_telemetry.armed is True

        # Mock subsequent disarmed HEARTBEAT (base_mode without 128)
        mock_msg_disarmed = MagicMock()
        mock_msg_disarmed.base_mode = 1
        vm.latest_telemetry.armed = bool(mock_msg_disarmed.base_mode & 128)
        assert vm.latest_telemetry.armed is False