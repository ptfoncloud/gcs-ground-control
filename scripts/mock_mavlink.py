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

print("[MOCK SITL - NOT REAL FEED AS OF 9/15/26] Broadcasting MAVLink packets to " \
"127.0.0.1:14550 at 20 hz . . . (Ctrl-C to exit)")

start_time = time.time()

try:
    while True: 
        now = time.time()
        t = now - start_time

        # GUIDED - needs to generate a dynamic flight profile like follower wld (simulated gentle climb and bank)
        sim_altitude_mm = int(max(0.0, (15.0 + 5.0 * math.sin(t * 0.5))) * 1000) #mm
        sim_pitch_rad = 0.08 * math.sin(t * 0.6)
        sim_roll_rad = 0.15 * math.cos(t * 0.6)
        sim_yaw_rad = (t * 0.2) % (2 * math.pi)
        sim_groundspeed_cms = int((4.5 + math.sin(t)) * 100) #cm/s per second! MATH!!  . . .  YAY!!
        sim_battery_mv = int(12400 - (t * 5)) #12.4V decaying

        # this is for when its armed in guided flight
        mav.mav.heartbeat_send(
            mavutil.mavlink.MAV_TYPE_QUADROTOR,
            mavutil.mavlink.MAV_AUTOPILOT_ARDUPILOTMEGA,
            mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED | mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4,
            # GUIDED MODE
            mavutil.mavlink.MAV_STATE_ACTIVE
        )

        # ATTITUDE 20hz
        mav.mav.attitude_send(
            int(t * 1000),
            sim_roll_rad,
            sim_pitch_rad,
            sim_yaw_rad,
            0.0, 0.0, 0.0
        )

        # Global Postion INT (10hz)
        mav.mav.global_position_int_send(
            int(t * 1000),
            339200000, # random lat
            -1184000000, # random lon
            sim_altitude_mm,
            sim_altitude_mm,
            sim_groundspeed_cms, 0, 0,
            int(math.degrees(sim_yaw_rad) * 100)
        )

        # SYS_STATUS (2hz) - general status stuff
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