import asyncio
from mavsdk import System
import time

async def run():
    # -- Connection string
    mavsdk_server_address = "localhost"
    port = 50051

    # -- Parameters
    takeoff_altitude = 5  # meters
    hover_duration = 10    # seconds

    # 1. Connect
    drone = System(mavsdk_server_address=mavsdk_server_address, port=port)
    print(f"Connecting to drone on: {mavsdk_server_address}:{port}")
    await drone.connect()

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("--> Link: OK")
            break
        await asyncio.sleep(1)

    # 2. Wait for GPS & EKF
    print("Waiting for EKF/GPS Readiness...")
    async for health in drone.telemetry.health():
        if health.is_armable and health.is_global_position_ok and health.is_home_position_ok:
            print("--> System Ready")
            break
        await asyncio.sleep(1)

    # 3. Arming with Verification
    print("-- Arming...")
    await drone.action.arm()
    
    # CRITICAL FIX: Wait until the drone confirms it is ARMED
    async for is_armed in drone.telemetry.armed():
        if is_armed:
            print("--> Confirmed: Drone is ARMED")
            break
        await asyncio.sleep(1)

    # 4. Guided Takeoff
    print(f"-- Executing Guided Takeoff to {takeoff_altitude}m...")
    await drone.action.set_takeoff_altitude(float(takeoff_altitude))
    await drone.action.takeoff()

    # 5. Wait for Altitude
    print("-- Waiting to reach altitude...")
    async for position in drone.telemetry.position():
        # Wait until we are at least 95% of the target altitude
        if position.relative_altitude_m >= takeoff_altitude * 0.95:
            print(f"--> Altitude Reached: {round(position.relative_altitude_m, 1)}m")
            break
        await asyncio.sleep(1)
        
    # 6. Hover for a specified duration
    print(f"Hovering for {hover_duration} seconds")
    await asyncio.sleep(hover_duration)

    # 7. Land the vehicle
    print("Landing...")
    await drone.action.land()

    # Wait until the vehicle has landed (altitude close to 0)
    print("Waiting for drone to land...")
    async for position in drone.telemetry.position():
        if position.relative_altitude_m < 0.5: # Consider landed when altitude is less than 0.5m
            print("--> Confirmed: Drone has landed")
            break
        await asyncio.sleep(1)

    print("Script complete.")

if __name__ == "__main__":
    asyncio.run(run())