# Totally different topic, 
# but everytime I see anything with MAV in it 
# I think of the Mars Ascent Vehicle from The Martian. 
# That movie is so cool, the book was slightly better though.
# You can ignore this message and enjoy parsing through my code now lol. \

# also if you TLDR the README.md 
# I programmed a lot of this from 10-2AM so there are silly bits but it hopefully works!
# :-)

import math
import time
import pymavlink 
from pymavlink import mavutil

# this binds the UDP client targeting the backend listener on port 14550.
mav = mavutil.mavlink_connection("udpout:127.0.0.1:14550", source_system=1, source_component=1)

# Windows Winsock fix: bind socket to an ephemeral local port so recvfrom() is valid
mav.port.bind(('', 0))

print("[MOCK SITL - NOT REAL FEED AS OF 9/15/26] Broadcasting MAVLink packets to " \
"127.0.0.1:14550 at 20 hz . . . (Ctrl-C to exit)")

# Flight state variables updated dynamically by uplink commands
is_armed = False
custom_mode = 4  # Default to GUIDED (mode 4 in ArduCopter)
altitude_m = 0.0
ground_speed_ms = 0.0

start_time = time.time()
loop_tick = 0  # increments once per 50ms loop iteration (20Hz)

try:
    while True: 
        now = time.time()
        t = now - start_time
        loop_tick += 1

        # --- DRAIN INCOMING UDP COMMAND BUFFER NON-BLOCKINGLY ---
        while True:
            try:
                msg = mav.recv_match(blocking=False)
            except (BlockingIOError, ConnectionResetError, OSError):
                # Catches Windows WSAECONNRESET (10054) when backend hasn't bound port yet
                break

            if not msg:
                break

            msg_type = msg.get_type()

            if msg_type == "COMMAND_LONG":
                if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
                    target_arm = bool(msg.param1 == 1.0)
                    if target_arm != is_armed:
                        is_armed = target_arm
                        state_str = "ARMED" if is_armed else "DISARMED"
                        print(f"[SITL RX] Propulsion Interlock -> {state_str}")

                    # Uplink MAVLink COMMAND_ACK confirmation
                    mav.mav.command_ack_send(
                        msg.command,
                        mavutil.mavlink.MAV_RESULT_ACCEPTED
                    )

            elif msg_type == "SET_MODE":
                custom_mode = msg.custom_mode
                print(f"[SITL RX] Mode Switched -> ID {custom_mode}")

        # GUIDED - needs to generate a dynamic flight profile like follower wld (simulated gentle climb and bank)
        if is_armed:
            # Climb and accelerate when armed
            altitude_m = min(altitude_m + 0.3, 50.0)
            ground_speed_ms = min(ground_speed_ms + 0.5, 12.0)
            sim_pitch_rad = 0.08 * math.sin(t * 0.6)
            sim_roll_rad = 0.15 * math.cos(t * 0.6)
            sim_yaw_rad = (t * 0.2) % (2 * math.pi)
        else:
            # Return to ground and zero out speed when disarmed
            altitude_m = max(altitude_m - 0.5, 0.0)
            ground_speed_ms = max(ground_speed_ms - 0.5, 0.0)
            sim_pitch_rad = 0.0
            sim_roll_rad = 0.0
            sim_yaw_rad = 0.0

        sim_altitude_mm = int(altitude_m * 1000) #mm
        sim_groundspeed_cms = int(ground_speed_ms * 100) #cm/s per second! MATH!!  . . .  YAY!!
        sim_battery_mv = int(12400 - (t * 5)) #12.4V decaying

        # this is for when its armed in guided flight
        base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
        if is_armed:
            base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED

        # HEARTBEAT 1hz (matches real ArduPilot behavior — it was
        # previously firing at the full 20hz loop rate)
        if loop_tick % 20 == 0:
            mav.mav.heartbeat_send(
                mavutil.mavlink.MAV_TYPE_QUADROTOR,
                mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
                base_mode,
                custom_mode,
                # GUIDED MODE
                mavutil.mavlink.MAV_STATE_ACTIVE if is_armed else mavutil.mavlink.MAV_STATE_STANDBY
            )

        # ATTITUDE 20hz — every loop tick
        mav.mav.attitude_send(
            int(t * 1000),
            sim_roll_rad,
            sim_pitch_rad,
            sim_yaw_rad,
            0.0, 0.0, 0.0
        )

        # Global Position INT 10hz — every other tick
        if loop_tick % 2 == 0:
            mav.mav.global_position_int_send(
                int(t * 1000),
                339200000, # random lat
                -1184000000, # random lon
                sim_altitude_mm,
                sim_altitude_mm,
                sim_groundspeed_cms, 0, 0,
                int(math.degrees(sim_yaw_rad) * 100)
            )

        # SYS_STATUS 2hz — every 10th tick
        if loop_tick % 10 == 0:
            mav.mav.sys_status_send(
                0,0,0,0,
                sim_battery_mv,
                -1,      # battery current unknown
                95,      # 95% remaining
                0 , 0 , 0 , 0 , 0 , 0
            )

        time.sleep(0.05) # 20hz loop rate

except KeyboardInterrupt:
    print("\n[MOCK SITL] Feeder stopped.")