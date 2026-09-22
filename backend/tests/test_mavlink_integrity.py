"""
All tests here drive VehicleManager._track_sequence(...) directly — the
actual production method extracted from the ingest loop in vehicle.py —
rather than a hand-copied "reference implementation" that could silently
drift from the real logic.
"""


class TestMavlinkSequenceMath:

    def test_nominal_continuous_stream(self, fresh_vehicle):
        """Sequential packets (N, N+1, N+2) must yield exactly zero dropped packets."""
        vm = fresh_vehicle
        for seq in range(100):
            vm._track_sequence(seq)

        assert vm.packets_rx == 100
        assert vm.packets_lost == 0
        assert vm.packet_loss_pct == 0.0

    def test_single_packet_drop(self, fresh_vehicle):
        """Skipping sequence 5 (sending 4 then 6) must record exactly 1 lost packet."""
        vm = fresh_vehicle
        for seq in [1, 2, 3, 4, 6, 7]:  # Packet 5 dropped in transit
            vm._track_sequence(seq)

        assert vm.packets_rx == 6
        assert vm.packets_lost == 1
        assert round(vm.packet_loss_pct, 2) == round((1 / 7) * 100, 2)

    def test_multi_packet_burst_loss(self, fresh_vehicle):
        """Burst drop from seq 10 to seq 15 represents 4 dropped frames (11, 12, 13, 14)."""
        vm = fresh_vehicle
        vm._track_sequence(10)
        vm._track_sequence(15)

        assert vm.packets_rx == 2
        assert vm.packets_lost == 4  # (15 - 10 - 1) % 256 = 4

    def test_uint8_rollover_nominal(self, fresh_vehicle):
        """Rollover from sequence 255 to sequence 0 without drops must record 0 loss."""
        vm = fresh_vehicle
        vm.last_seq, vm.packets_rx, vm.packets_lost = 255, 100, 0

        vm._track_sequence(0)

        # (0 - 255 - 1) % 256 = -256 % 256 = 0
        assert vm.packets_rx == 101
        assert vm.packets_lost == 0

    def test_uint8_rollover_with_loss(self, fresh_vehicle):
        """
        Rollover dropping frames across the boundary:
        Last seen 254 -> Current 2. Dropped: 255, 0, 1 (total 3 packets).
        """
        vm = fresh_vehicle
        vm.last_seq, vm.packets_rx, vm.packets_lost = 254, 50, 0

        vm._track_sequence(2)

        # (2 - 254 - 1) % 256 = -253 % 256 = 3
        assert vm.packets_rx == 51
        assert vm.packets_lost == 3

    def test_duplicate_frame_rejection(self, fresh_vehicle):
        """Duplicate packet arrival (seq 40 immediately followed by seq 40) must not inflate loss."""
        vm = fresh_vehicle
        vm._track_sequence(40)
        vm._track_sequence(40)

        assert vm.packets_rx == 2
        assert vm.packets_lost == 0
        assert vm.last_seq == 40  # baseline unaffected by the duplicate

    def test_reordered_packet_does_not_corrupt_baseline(self, fresh_vehicle):
        """
        Regression test for the out-of-order handling bug: a packet
        arriving late/out of order (a lower sequence number than the last
        one seen, with no wraparound involved) must not rewind `last_seq`
        — otherwise the *next* correctly-ordered packet computes its delta
        against the wrong baseline and reports phantom loss.

        Sequence arrival order: 10, 11, 9 (reordered), 12.
        Expected: 9 is ignored for baseline purposes; 12 is recognized as
        immediately following 11 (0 additional loss), not as following 9
        (which would report 2 lost packets that were never actually lost).
        """
        vm = fresh_vehicle
        vm._track_sequence(10)
        vm._track_sequence(11)
        vm._track_sequence(9)  # arrives late, out of order
        vm._track_sequence(12)

        assert vm.last_seq == 12
        assert vm.packets_lost == 0
        assert vm.packets_rx == 4


class TestVehicleManagerPacketIntegration:

    def test_vehicle_manager_ingestion_updates_loss(self, fresh_vehicle):
        """Verifies VehicleManager state updates match packet calculation on simulated incoming feed."""
        vm = fresh_vehicle

        for seq in [0, 1, 2, 5]:  # Packets 3 and 4 dropped
            vm._track_sequence(seq)

        assert vm.packets_rx == 4
        assert vm.packets_lost == 2
        assert vm.packet_loss_pct == 33.33
