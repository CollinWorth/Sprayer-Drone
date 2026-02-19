import asyncio
import json
import sys
from drone_actions import Drone
from mavsdk.mission import MissionItem

MAV_CMD_NAV_WAYPOINT = 16
MAV_CMD_NAV_TAKEOFF = 22

async def parse_plan_file(file_path): """
    Parses a QGroundControl .plan file and returns a list of MissionItem objects
    and a boolean indicating if a takeoff command is present.
    """
    try:
        with open(file_path, 'r') as f:
            plan_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Plan file not found at {file_path}")
        return None, False
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return None, False

    mission_items = []
    has_takeoff_command = False
    
    if 'mission' in plan_data and 'items' in plan_data['mission']:
        cruise_speed = plan_data['mission'].get('cruiseSpeed', 8.0)

        for i, item in enumerate(plan_data['mission']['items']):
            item_type = item.get('type')
            if item_type != 'SimpleItem':
                continue
                
            command = item.get('command')
            params = item.get('params', [])

            if command == MAV_CMD_NAV_WAYPOINT and len(params) >= 7:
                lat = params[4]
                lon = params[5]
                alt = params[6]
                
                mission_items.append(
                    MissionItem(
                        lat,
                        lon,
                        alt,
                        cruise_speed,
                        True,  # is_fly_through
                        float('nan'), # gimbal_pitch_deg
                        float('nan'), # gimbal_yaw_deg
                        MissionItem.CameraAction.NONE,
                        float('nan'), # loiter_time_s
                        float('nan'), # camera_photo_interval_s
                        params[1] if params and len(params) > 1 and params[1] > 0 else float('nan'), # acceptance_radius
                        float('nan'), # yaw_deg
                        float('nan'), # camera_photo_distance_m
                        MissionItem.VehicleAction.NONE
                    )
                )
            elif command == MAV_CMD_NAV_TAKEOFF and len(params) >= 7:
                if i == 0:
                    has_takeoff_command = True
                lat = params[4]
                lon = params[5]
                alt = params[6]
                mission_items.append(
                    MissionItem(
                        lat,
                        lon,
                        alt,
                        float('nan'), # speed
                        False, # is_fly_through
                        float('nan'), # gimbal_pitch_deg
                        float('nan'), # gimbal_yaw_deg
                        MissionItem.CameraAction.NONE,
                        float('nan'), # loiter_time_s
                        float('nan'), # camera_photo_interval_s
                        float('nan'), # acceptance_radius
                        float('nan'), # yaw_deg
                        float('nan'), # camera_photo_distance_m
                        MissionItem.VehicleAction.NONE
                    )
                )

    return mission_items, has_takeoff_command

async def run(plan_file):
    """
    This script reads a QGC mission plan, uploads it to the drone, and executes it.
    """
    drone = Drone()

    if not await drone.connect():
        print("Failed to connect to the drone. Exiting.")
        return

    await drone.wait_for_readiness()

    mission_items, has_takeoff_command = await parse_plan_file(plan_file)

    if not mission_items:
        print(f"No mission items found or error parsing {plan_file}. Exiting.")
        return
        
    print(f"Loaded {len(mission_items)} mission items from {plan_file}.")
    if has_takeoff_command:
        print("Mission plan includes a takeoff command.")

    await drone.upload_mission(mission_items)

    await drone.arm()

    if not has_takeoff_command:
        print("No takeoff command in mission, taking off manually to 10m.")
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
    plan_file_path = "mission.plan"
    if len(sys.argv) > 1:
        plan_file_path = sys.argv[1]
    else:
        print("please provide file .plan as parameter")
    asyncio.run(run(plan_file_path))
