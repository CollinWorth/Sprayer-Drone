import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System
import sys

# Load default from .env
load_dotenv()
CONNECTION_STR = os.getenv("CONNECTION_STRING")
MISSION_PATH = "/Users/collin/drone/Sprayer-Drone/missions"
MISSION_FILE_RAW = os.getenv("MISSION_FILE")

# Override MISSION_FILE if an argument is passed: python3 script.py field_2.plan
if len(sys.argv) > 1:
    MISSION_FILE = sys.argv[1]
else:
    MISSION_FILE = os.path.join(MISSION_PATH,MISSION_FILE_RAW)

    # MISSION_FILE = os.path.join("/Users/collin/drone/Sprayer-Drone/src/flight", "parker_farm_1.plan")


async def run():
    drone = System()
    
    print(f"Connecting to drone at {CONNECTION_STR}...")
    await drone.connect(system_address=CONNECTION_STR)

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # 1. SETUP: Import and Upload Mission to Cube EEPROM
    print(f"Importing {MISSION_FILE}...")
    mission_data = await drone.mission_raw.import_qgroundcontrol_mission(MISSION_FILE)
    
    print(f"Uploading {len(mission_data.mission_items)} items to Cube...")
    await drone.mission_raw.upload_mission(mission_data.mission_items)
    
    # 2. LAUNCH
    print("Arming...")
    # Note: Cube will reject arming if GPS lock isn't solid or EKF is unhappy
    await drone.action.arm()
    
    print("Starting Mission...")
    await drone.mission.start_mission()

    # 3. THE SMART LOOP
    # The script now runs headless and monitors status
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: {mission_progress.current}/{mission_progress.total}")
        
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

if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Script stopped by user.")
