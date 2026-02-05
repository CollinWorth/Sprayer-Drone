import asyncio
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from mavsdk.telemetry import FlightMode

async def run():
    # 1. Connect
    drone = System(mavsdk_server_address="localhost", port=50051)
    await drone.connect()

    print("Waiting for drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("--> Link: OK")
            break

    # 2. Wait for GPS & EKF
    print("Waiting for EKF/GPS Readiness...")
    async for health in drone.telemetry.health():
        if health.is_armable and health.is_global_position_ok:
            print("--> System Ready")
            break

    # 3. Create Mission (Standard Waypoints ONLY)
    print("-- Generating Mission Plan (Airborne segments only)")
    mission_items = [
        # WP 1: A normal point in the sky. 
        # Since we will be airborne when we start, we don't need a TAKEOFF item.
        # latitude, longitude, altitude, speed, autoContinue, param1, param2, param3, param4, cameraAction, param6, param7, vehicleAction
        MissionItem(
            -35.363761, 149.165690, 10, 8, True, float('nan'), float('nan'), 
            MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'), 
            float('nan'), float('nan'), MissionItem.VehicleAction.NONE
        ),
        # WP 2
        MissionItem(
           -35.363551, 149.164953, 10, 8, True, float('nan'), float('nan'), 
            MissionItem.CameraAction.NONE, float('nan'), float('nan'), float('nan'), 
            float('nan'), float('nan'), MissionItem.VehicleAction.NONE
        )
    ]
    await drone.mission.upload_mission(MissionPlan(mission_items))
    print("--> Mission Uploaded")

    # 4. Arming with Verification
    print("-- Arming...")
    await drone.action.arm()
    
    # CRITICAL FIX: Wait until the drone confirms it is ARMED
    async for is_armed in drone.telemetry.armed():
        if is_armed:
            print("--> Confirmed: Drone is ARMED")
            break

    # 5. Guided Takeoff (Get us into the air first)
    print("-- Executing Guided Takeoff to 10m...")
    await drone.action.set_takeoff_altitude(10.0)
    
    try:
        await drone.action.takeoff()
    except Exception as e:
        print(f"Takeoff Exception: {e}")
        # If it fails, force Guided mode and retry
        print("Retrying Takeoff via Forced Mode Switch...")
        await drone.action.hold()
        await asyncio.sleep(1)
        await drone.action.takeoff()

    # 6. Wait for Altitude
    print("-- Waiting to reach altitude...")
    async for position in drone.telemetry.position():
        # Wait until we are at least 8 meters up
        if position.relative_altitude_m > 8.0:
            print(f"--> Altitude Reached: {round(position.relative_altitude_m, 1)}m")
            break
        
    # 7. Start the Autonomous Mission
    print("-- Switching to AUTO Mode (Starting Mission)")
    print("-- Resetting Mission Index to 0...")
    await drone.mission.set_current_mission_item(0)

    # Give the drone 2 seconds to "Rewind" its internal brain
    await asyncio.sleep(2)

    await drone.mission.set_current_mission_item(0)

    await drone.mission.start_mission()

    # 8. Monitor Progress
    async for progress in drone.mission.mission_progress():
        print(f"   [Mission] Waypoint {progress.current}/{progress.total}")
        if progress.current == progress.total:
            print("-- Mission Complete: Returning to Launch")
            await drone.action.return_to_launch()
            break

if __name__ == "__main__":
    asyncio.run(run())
