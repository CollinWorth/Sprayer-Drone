import asyncio
from drone_actions import Drone
from mavsdk.mission import MissionItem

async def run():
    """
    This script demonstrates how to use the Drone class to perform a simple mission.
    """
    drone = Drone()

    if not await drone.connect():
        print("Failed to connect to the drone. Exiting.")
        return

    await drone.wait_for_readiness()

    # Create and upload a simple mission
    mission_items = [
        MissionItem(-35.363761, 149.165690, 10, 8, True, float('nan'), float('nan'),
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'),
                    float('nan'), float('nan'), MissionItem.VehicleAction.NONE),
        MissionItem(-35.363551, 149.164953, 10, 8, True, float('nan'), float('nan'),
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'),
                    float('nan'), float('nan'), MissionItem.VehicleAction.NONE),
        MissionItem(-35.363261, 149.165230, 10, 8, True, float('nan'), float('nan'), 
                    MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'), 
                    float('nan'), float('nan'), MissionItem.VehicleAction.NONE)
    ]
    await drone.upload_mission(mission_items)

    await drone.arm()

    await drone.takeoff(altitude=10.0)

    await drone.start_mission()

    await drone.monitor_mission_progress()

    await drone.return_to_launch()

    # Wait for the drone to land
    async for in_air in drone.system.telemetry.in_air():
        if not in_air:
            print("--> Drone has landed.")
            break
    
    await drone.disarm()

    await drone.shutdown()
    print("--- Flight Test Complete ---")

if __name__ == "__main__":
    asyncio.run(run())
