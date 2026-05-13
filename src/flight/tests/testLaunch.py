import asyncio
import argparse
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from drone_actions import Drone

async def run(takeoff_altitude: float, hover_duration: float):
    drone = Drone()
    await drone.connect()
    await drone.wait_for_readiness()
    await drone.arm()
    await drone.takeoff(altitude=takeoff_altitude)
    print(f"Hovering for {hover_duration} seconds")
    await asyncio.sleep(hover_duration)
    await drone.land()
    print("Script complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Takeoff, hover, and land.")
    parser.add_argument("height", type=float, help="Takeoff altitude in meters")
    parser.add_argument("time", type=float, help="Hover duration in seconds")
    args = parser.parse_args()

    asyncio.run(run(takeoff_altitude=args.height, hover_duration=args.time))
