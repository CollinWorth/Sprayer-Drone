import asyncio
from drone_actions import Drone

async def run():
    drone = Drone()
    await drone.connect()
    
    # Start the error listener in the background so it catches 
    # messages the moment they happen
    asyncio.create_task(drone.log_status_messages())

    # This might hang if you're indoors without a GPS lock
    await drone.wait_for_readiness() 
    
    await drone.arm()
    
    await asyncio.sleep(5)
    await drone.disarm()
if __name__ == "__main__":
    asyncio.run(run())
