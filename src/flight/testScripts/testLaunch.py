import asyncio
from drone_actions import Drone

async def run():
    # -- Parameters
    takeoff_altitude = 5  # meters
    hover_duration = 10    # seconds

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
    asyncio.run(run())