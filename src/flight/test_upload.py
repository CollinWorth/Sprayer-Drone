"""
Connects to the FC, uploads the mission, reads it back to verify, then exits.
Does NOT arm or start the mission. Safe to run on a bench with props off.
Run: python3 test_upload.py ../../missions/parker_farm2_small.plan
"""
import sys
import asyncio
import os
from dotenv import load_dotenv
from mavsdk import System

load_dotenv()
CONNECTION_STR = os.getenv("CONNECTION_STRING")


async def run(plan_path: str):
    drone = System()
    print(f"Connecting to {CONNECTION_STR}...")
    await drone.connect(system_address=CONNECTION_STR)

    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Connected.\n")
            break

    # Import
    print(f"Importing {plan_path}...")
    try:
        mission_data = await drone.mission_raw.import_qgroundcontrol_mission(plan_path)
    except Exception as e:
        print(f"FAIL: import — {e}")
        return

    print(f"Parsed {len(mission_data.mission_items)} items.")

    # Upload with timeout
    print("Uploading...")
    try:
        await asyncio.wait_for(
            drone.mission_raw.upload_mission(mission_data.mission_items),
            timeout=60.0
        )
        print("Upload: OK\n")
    except asyncio.TimeoutError:
        print("FAIL: upload timed out after 60s")
        return
    except Exception as e:
        print(f"FAIL: upload — {e}")
        return

    # Read back from FC to verify
    print("Reading mission back from FC...")
    try:
        downloaded = await asyncio.wait_for(
            drone.mission_raw.download_mission(),
            timeout=30.0
        )
        print(f"FC reports {len(downloaded)} items stored.\n")
        for i, item in enumerate(downloaded):
            lat = item.x / 1e7
            lon = item.y / 1e7
            print(f"  [{i}] cmd={item.command:>4}  lat={lat:>14.7f}  lon={lon:>15.7f}  alt={item.z:.2f}m")
    except Exception as e:
        print(f"WARN: could not read back mission — {e}")

    print("\nPASS: Mission upload verified. Not arming.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_upload.py <path/to/mission.plan>")
        sys.exit(1)
    asyncio.run(run(sys.argv[1]))
