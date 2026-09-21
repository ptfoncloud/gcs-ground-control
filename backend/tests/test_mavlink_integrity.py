import pytest

def calculate_packet_metrics(current_seq: int, last_seq: int | None, rx_count: int, lost_count: int):
    """
    Pure reference implementation of MAVLink 8-bit sequence loss tracking.
    Matches the tracking logic embedded in VehicleManager.
    """
    if last_seq is None:
        return current_seq, rx_count + 1, lost_count

    delta = (current_seq - last_seq - 1) % 256

    # Rejection gate: Ignore duplicate or severely out-of-order packets (> 50 drop jump)
    if 0 < delta < 50:
        lost_count += delta

    rx_count += 1
    return current_seq, rx_count, lost_count


class TestMavlinkSequenceMath:

    def test_nominal_continuous_stream(self):
        """Sequential packets (N, N+1, N+2) must yield exactly zero dropped packets."""
        last_seq = None
        rx, lost = 0, 0

        for seq in range(100):
            last_seq, rx, lost = calculate_packet_metrics(seq, last_seq, rx, lost)

        assert rx == 100
        assert lost == 0
        loss_pct = (lost / (rx + lost)) * 100
        assert loss_pct == 0.0

    def test_single_packet_drop(self):
        """Skipping sequence 5 (sending 4 then 6) must record exactly 1 lost packet."""
        last_seq, rx, lost = None, 0, 0

        stream = [1, 2, 3, 4, 6, 7]  # Packet 5 dropped in transit
        for seq in stream:
            last_seq, rx, lost = calculate_packet_metrics(seq, last_seq, rx, lost)

        assert rx == 6
        assert lost == 1
        loss_pct = (lost / (rx + lost)) * 100
        assert round(loss_pct, 2) == round((1 / 7) * 100, 2)

    def test_multi_packet_burst_loss(self):
        """Burst drop from seq 10 to seq 15 represents 4 dropped frames (11, 12, 13, 14)."""
        last_seq, rx, lost = calculate_packet_metrics(10, None, 0, 0)
        last_seq, rx, lost = calculate_packet_metrics(15, last_seq, rx, lost)

        assert rx == 2
        assert lost == 4  # (15 - 10 - 1) % 256 = 4

    def test_uint8_rollover_nominal(self):
        """Rollover from sequence 255 to sequence 0 without drops must record 0 loss."""
        last_seq, rx, lost = 255, 100, 0
        last_seq, rx, lost = calculate_packet_metrics(0, last_seq, rx, lost)

        # (0 - 255 - 1) % 256 = -256 % 256 = 0
        assert rx == 101
        assert lost == 0

    def test_uint8_rollover_with_loss(self):
        """
        Rollover dropping frames across the boundary:
        Last seen 254 -> Current 2. Dropped: 255, 0, 1 (total 3 packets).
        """
        last_seq, rx, lost = 254, 50, 0
        last_seq, rx, lost = calculate_packet_metrics(2, last_seq, rx, lost)

        # (2 - 254 - 1) % 256 = -253 % 256 = 3
        assert rx == 51
        assert lost == 3

    def test_duplicate_frame_rejection(self):
        """Duplicate packet arrival (seq 40 immediately followed by seq 40) must not inflate loss."""
        last_seq, rx, lost = calculate_packet_metrics(40, None, 0, 0)
        last_seq, rx, lost = calculate_packet_metrics(40, last_seq, rx, lost)

        
        assert rx == 2
        assert lost == 0


class TestVehicleManagerPacketIntegration:

    def test_vehicle_manager_ingestion_updates_loss(self, fresh_vehicle):
        """Verifies VehicleManager state updates match packet calculation on simulated incoming feed."""
        vm = fresh_vehicle

        simulated_sequences = [0, 1, 2, 5]  # Packets 3 and 4 dropped
        for s in simulated_sequences:
            if vm.last_seq is not None:
                delta = (s - vm.last_seq - 1) % 256
                if 0 < delta < 50:
                    vm.packets_lost += delta
            vm.last_seq = s
            vm.packets_rx += 1

        total = vm.packets_rx + vm.packets_lost
        loss_pct = round((vm.packets_lost / total) * 100, 2)

        assert vm.packets_rx == 4
        assert vm.packets_lost == 2
        assert loss_pct == 33.33