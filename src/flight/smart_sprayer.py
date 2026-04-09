import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System
from mavsdk.telemetry import FlightMode
import sys

# Load default from .env
load_dotenv()
CONNECTION_STR = os.getenv("CONNECTION_STRING")
MISSION_PATH = os.getenv("MISSION_PATH", "/home/pi/missions")
MISSION_FILE_RAW = os.getenv("MISSION_FILE")

# Override MISSION_FILE if an argument is passed: python3 script.py field_2.plan
if len(sys.argv) > 1:
    MISSION_FILE = os.path.join(MISSION_PATH, sys.argv[1])
elif MISSION_FILE_RAW:
    MISSION_FILE = os.path.join(MISSION_PATH, MISSION_FILE_RAW)
else:
    print("ERROR: No mission file specified. Set MISSION_FILE in .env or pass as argument.")
    sys.exit(1)


async def monitor_flight_mode(drone, mode_event):
    """Background task: sets mode_event when RC switches out of mission mode."""
    async for flight_mode in drone.telemetry.flight_mode():
        if flight_mode != FlightMode.MISSION:
            print(f"[Mode Change] Flight mode: {flight_mode} — RC may have taken over")
            mode_event.set()
        else:
            mode_event.clear()


async def wait_for_readiness(drone, timeout_s=120):
    """Wait for GPS lock and EKF before arming. Exits after timeout_s seconds."""
    print("Waiting for GPS and EKF readiness...")
    try:
        async with asyncio.timeout(timeout_s):
            async for health in drone.telemetry.health():
                if health.is_armable and health.is_global_position_ok:
                    print("System ready.")
                    return True
    except TimeoutError:
        print(f"ERROR: Drone not ready after {timeout_s}s. Check GPS and EKF status.")
        return False
    return False


async def arm_and_confirm(drone):
    """Send arm command and wait until the drone reports armed. Returns False on failure."""
    print("Arming...")
    try:
        await drone.action.arm()
    except Exception as e:
        print(f"ERROR: Arming failed — {e}")
        return False

    async for is_armed in drone.telemetry.armed():
        if is_armed:
            print("Drone armed.")
            return True
    return False


async def run():
    drone = System()

    print(f"Connecting to drone at {CONNECTION_STR}...")
    await drone.connect(system_address=CONNECTION_STR)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    ready = await wait_for_readiness(drone)
    if not ready:
        return

    # 1. SETUP: Import and Upload Mission
    print(f"Importing {MISSION_FILE}...")
    try:
        mission_data = await drone.mission_raw.import_qgroundcontrol_mission(MISSION_FILE)
    except Exception as e:
        print(f"ERROR: Failed to import mission file — {e}")
        return

    print(f"Uploading {len(mission_data.mission_items)} items...")
    try:
        await drone.mission_raw.upload_mission(mission_data.mission_items)
    except Exception as e:
        print(f"ERROR: Failed to upload mission — {e}")
        return

    # 2. LAUNCH
    armed = await arm_and_confirm(drone)
    if not armed:
        return

    print("Starting Mission...")
    try:
        await drone.mission.start_mission()
    except Exception as e:
        print(f"ERROR: Failed to start mission — {e}")
        await drone.action.disarm()
        return

    # Track RC takeover
    rc_took_over = asyncio.Event()
    asyncio.create_task(monitor_flight_mode(drone, rc_took_over))

    # 3. THE SMART LOOP
    # Uses mission_raw.mission_progress() to match how the mission was uploaded
    async for mission_progress in drone.mission_raw.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")

        if rc_took_over.is_set():
            print("[RC Takeover] Paused — waiting for mission to resume...")

        # --- FUTURE VISION LOGIC GOES HERE ---
        # Example:
        # if vision_system.target_detected():
        #     await drone.action.hold()
        #     await do_spray_action()
        #     await drone.mission.start_mission()

        if mission_progress.total > 0 and mission_progress.current == mission_progress.total:
            print("Final waypoint reached.")
            break

    # Mission plan already ends with RTL (command 20), but send it explicitly
    # in case the loop exits early (e.g. Ctrl+C caught above the try block)
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
