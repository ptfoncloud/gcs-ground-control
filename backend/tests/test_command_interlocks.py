import pytest
from unittest.mock import MagicMock
from app.vehicle import vehicle_manager


class TestCommandInterlocks:

    @pytest.mark.asyncio
    async def test_arm_command_dispatch_does_not_optimistically_arm(self, async_client):
        """
        Aerospace Interlock Safety:
        Dispatching POST /api/command {command: ARM} must return 200 ACK
        indicating transmission, but vehicle_manager.latest_telemetry.armed
        must REMAIN False until the vehicle authoritatively downlinks an
        armed HEARTBEAT (base_mode bitmask 0x80).

        Hits the actual canonical endpoint (/api/command via the mounted
        router) rather than the old duplicate /api/command/arm path that
        used to live directly in main.py.
        """
        vehicle_manager.latest_telemetry.armed = False
        vehicle_manager.master = MagicMock()  # Mock MAVLink UDP connection

        response = await async_client.post("/api/command", json={"command": "ARM", "force": False})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ACK"
        assert data["dispatched"] == "ARM"

        # Critical assertion: UI/Backend MUST NOT optimistically toggle state
        assert vehicle_manager.latest_telemetry.armed is False

    @pytest.mark.asyncio
    async def test_force_disarm_actually_sends_the_force_flag(self, async_client):
        """
        The "FORCE DISARM" control must dispatch MAV_CMD_COMPONENT_ARM_DISARM
        with the MAVLink force magic number (param2 = 21196) — a plain
        DISARM with force=False silently omitted (the original bug) would
        never reach this code path.
        """
        mock_master = MagicMock()
        vehicle_manager.master = mock_master

        response = await async_client.post("/api/command", json={"command": "DISARM", "force": True})

        assert response.status_code == 200
        assert response.json()["status"] == "ACK"

        _, kwargs = mock_master.mav.command_long_send.call_args
        sent_params = mock_master.mav.command_long_send.call_args[0]
        # signature: (target_sys, target_comp, command, confirmation, param1, param2, ...)
        assert sent_params[5] == 21196.0  # param2 == force-arm/disarm magic number

    @pytest.mark.asyncio
    async def test_unsupported_flight_mode_is_rejected_not_dispatched(self, async_client):
        """
        A mode string outside the supported set must be rejected with 422
        by CommandRequest's schema validation — it must never reach the
        vehicle layer and silently fall back to mode 0.
        """
        vehicle_manager.master = MagicMock()

        response = await async_client.post(
            "/api/command", json={"command": "SET_MODE", "mode": "BOGUS_MODE"}
        )

        assert response.status_code == 422
        vehicle_manager.master.mav.set_mode_send.assert_not_called()

    def test_set_mode_raises_for_unmapped_mode_name(self):
        """
        Defense in depth below the API layer: VehicleManager.set_mode itself
        must still reject an unrecognized mode (e.g. if called directly,
        such as from the gesture classifier) instead of defaulting to 0.
        """
        vm = vehicle_manager
        vm.master = MagicMock()
        vm.master.mode_mapping = MagicMock(return_value=None)

        with pytest.raises(ValueError):
            vm.set_mode("NOT_A_REAL_MODE")

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
        Simulates arrival of a real MAVLink HEARTBEAT message and calls the
        ACTUAL production handler (VehicleManager._handle_heartbeat) —
        not a reimplementation of the bitmask check inline in the test.
        State must transition to armed ONLY when MAV_MODE_FLAG_SAFETY_ARMED
        (128) is present in base_mode.
        """
        vm = fresh_vehicle
        assert vm.latest_telemetry.armed is False

        mock_msg_armed = MagicMock()
        mock_msg_armed.base_mode = 128 | 1  # Armed + Custom Mode enabled
        mock_msg_armed.custom_mode = 4

        vm._handle_heartbeat(mock_msg_armed)
        assert vm.latest_telemetry.armed is True
        assert vm.latest_telemetry.flight_mode == "GUIDED"

        mock_msg_disarmed = MagicMock()
        mock_msg_disarmed.base_mode = 1
        mock_msg_disarmed.custom_mode = 0

        vm._handle_heartbeat(mock_msg_disarmed)
        assert vm.latest_telemetry.armed is False
