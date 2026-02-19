import asyncio
import sys
import select
from mavsdk import System

# --- CONFIGURATION ---
MISSION_FILE = "parker_farm_1.plan" # Ensure this file exists
CONNECTION_STR = "udp://:14540" # Simulator

# --- MOCK VISION SYSTEM (Modified for keyboard input) ---
# In real life, this would be your YOLO/OpenCV function
def check_keyboard_input():
    # Check if there's input waiting
    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        if line == "":  # Enter key pressed
            return True
    return False

async def run():
    drone = System()
    await drone.connect(system_address=CONNECTION_STR)

    print("Waiting for drone...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone connected!")
            break

    # 1. SETUP: Import and Upload Mission
    print("Importing QGC Plan...")
    mission_data = await drone.mission_raw.import_qgroundcontrol_mission(MISSION_FILE)
    print(f"Uploading {len(mission_data.mission_items)} items...")
    await drone.mission_raw.upload_mission(mission_data.mission_items)
    
    # 2. LAUNCH
    print("Arming...")
    await drone.action.arm()
    
    print("Starting Mission...")
    await drone.mission.start_mission()

    # 3. THE SMART LOOP
    # We poll the vision system constantly while the mission flies
    while True:
        # Check if mission is finished
        mission_progress = await drone.mission.is_mission_finished()
        if mission_progress:
            print("Survey Complete!")
            break

        # --- VISION CHECK ---
        if check_keyboard_input():
            print("!!! KEYBOARD INTERRUPT DETECTED - INTERRUPTING MISSION !!!")
            
            # A. PAUSE (Switch to Hold Mode)
            # This freezes the drone in place (GPS Hold)
            await drone.action.hold()
            
            # B. PERFORM ACTION (Spray)
            print(">>> SPRAYING TARGET...")
            # Real code: toggle a relay or servo here
            # await drone.action.set_actuator(1, 0.9) 
            await asyncio.sleep(2) # Simulate spray duration
            print(">>> SPRAY COMPLETE.")

            # C. RESUME (Switch back to Mission Mode)
            # ArduPilot automatically remembers where it was in the mission
            print("Resuming Mission...")
            await drone.mission.start_mission()

        # Small sleep to prevent CPU hogging
        await asyncio.sleep(0.1)

    # End
    await drone.action.return_to_launch()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())

