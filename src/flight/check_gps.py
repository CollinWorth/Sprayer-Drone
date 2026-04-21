"""
Connects and prints GPS fix, satellite count, and health flags. Then exits.
Run: python3 check_gps.py
"""
import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System

load_dotenv()


async def run():
    drone = System()
    await drone.connect(system_address=os.getenv("CONNECTION_STRING"))

    async for state in drone.core.connection_state():
        if state.is_connected:
            break

    async for gps in drone.telemetry.gps_info():
        print(f"Fix:        {gps.fix_type}")
        print(f"Satellites: {gps.num_satellites}")
        break

    async for health in drone.telemetry.health():
        print(f"Global pos OK: {health.is_global_position_ok}")
        print(f"Armable:       {health.is_armable}")
        break


asyncio.run(run())
