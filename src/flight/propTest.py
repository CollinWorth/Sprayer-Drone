import asyncio
from drone_actions import Drone

async def run():
    drone = Drone()
    await drone.connect()
    await drone.wait_for_readiness()
    await drone.arm()
    print("--- Props spinning for 5 seconds ---")
    await asyncio.sleep(5)
    await drone.disarm()

if __name__ == "__main__":
    asyncio.run(run())