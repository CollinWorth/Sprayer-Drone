import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System
import sys

# Load default from .env
load_dotenv()
CONNECTION_STR = os.getenv("CONNECTION_STRING")
MISSION_PATH = os.getenv("MISSION_PATH", "/home/pi/missions")
MISSION_FILE_RAW = os.getenv("MISSION_FILE")

# Override MISSION_FILE if an argument is passed: python3 script.py field_2.plan
if len(sys.argv) > 1:
    MISSION_FILE = os.path.join(MISSION_PATH, sys.argv[1])
else:
    MISSION_FILE = os.path.join(MISSION_PATH, MISSION_FILE_RAW)


async def monitor_flight_mode(drone, mode_event):
    """Background task: sets mode_event when RC switches out of mission mode."""
    async for flight_mode in drone.telemetry.flight_mode():
        mode_name = str(flight_mode)
        if "MISSION" not in mode_name:
            print(f"[Mode Change] Flight mode changed to: {mode_name} — RC may have taken over")
            mode_event.set()
        else:
            mode_event.clear()


async def wait_for_readiness(drone):
    """Wait for GPS lock and EKF before arming."""
    print("Waiting for GPS and EKF readiness...")
    async for health in drone.telemetry.health():
        if health.is_armable and health.is_global_position_ok:
            print("System ready.")
            break


async def arm_and_confirm(drone):
    """Send arm command and wait until the drone reports armed."""
    print("Arming...")
    await drone.action.arm()
    async for is_armed in drone.telemetry.armed():
        if is_armed:
            print("Drone armed.")
            break


async def run():
    drone = System()

    print(f"Connecting to drone at {CONNECTION_STR}...")
    await drone.connect(system_address=CONNECTION_STR)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    await wait_for_readiness(drone)

    # 1. SETUP: Import and Upload Mission
    print(f"Importing {MISSION_FILE}...")
    mission_data = await drone.mission_raw.import_qgroundcontrol_mission(MISSION_FILE)

    print(f"Uploading {len(mission_data.mission_items)} items...")
    await drone.mission_raw.upload_mission(mission_data.mission_items)

    # 2. LAUNCH
    await arm_and_confirm(drone)

    print("Starting Mission...")
    await drone.mission.start_mission()

    # Track RC takeover
    rc_took_over = asyncio.Event()
    asyncio.create_task(monitor_flight_mode(drone, rc_took_over))

    # 3. THE SMART LOOP
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")

        if rc_took_over.is_set():
            print("[RC Takeover] Waiting for RC to return control or mission to resume...")

        # --- FUTURE VISION LOGIC GOES HERE ---
        # Example:
        # if vision_system.target_detected():
        #     await drone.action.hold()
        #     await do_spray_action()
        #     await drone.mission.start_mission()

        if mission_progress.current == mission_progress.total:
            print("Final waypoint reached.")
            break

    print("Mission Complete! Initiating RTL...")
    await drone.action.return_to_launch()

    print("Waiting for landing...")
    async for in_air in drone.telemetry.in_air():
        if not in_air:
            print("Drone landed.")
            break

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script stopped by user.")
