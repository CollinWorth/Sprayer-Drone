import asyncio
import os
import json
from dotenv import load_dotenv
from mavsdk import System
from mavsdk.mission import MissionItem, MissionPlan
from mavsdk.mission_raw import MissionItem as MissionRawItem
from mavsdk.telemetry import MAV_CMD

def convert_mission_raw_item_to_mission_item(raw_item: MissionRawItem) -> MissionItem:
    """
    Converts a mavsdk.mission_raw.MissionItem to a mavsdk.mission.MissionItem.

    Args:
        raw_item: The mission_raw.MissionItem object to convert.

    Returns:
        A new mavsdk.mission.MissionItem object.
    """

    # Initialize with default values or values that can be directly mapped
    mission_item = MissionItem(
        latitude_deg=raw_item.x / 1e7,  # x is latitude scaled by 1e7
        longitude_deg=raw_item.y / 1e7, # y is longitude scaled by 1e7
        relative_altitude_m=raw_item.z, # z is altitude in meters
        speed_m_s=float('nan'),         # Default to NaN, will be set if command specifies
        is_fly_through=False,           # Default, will be set if command specifies
        gimbal_pitch_deg=float('nan'),  # Default to NaN
        gimbal_yaw_deg=float('nan'),    # Default to NaN
        camera_action=MissionItem.CameraAction.NONE,
        loiter_time_s=float('nan'),
        camera_photo_interval_s=float('nan'),
        acceptance_radius_m=float('nan'),
        yaw_deg=float('nan'),
        camera_photo_distance_m=float('nan'),
        vehicle_action=MissionItem.VehicleAction.NONE
    )

    # Interpret MAVLink command and parameters
    if raw_item.command == MAV_CMD.MAV_CMD_NAV_WAYPOINT:
        mission_item.is_fly_through = (raw_item.param3 == 0)
        mission_item.acceptance_radius_m = raw_item.param2
        mission_item.yaw_deg = raw_item.param4

    elif raw_item.command == MAV_CMD.MAV_CMD_DO_CHANGE_SPEED:
        mission_item.speed_m_s = raw_item.param2

    elif raw_item.command == MAV_CMD.MAV_CMD_NAV_LOITER_TIME:
        mission_item.loiter_time_s = raw_item.param1
        mission_item.acceptance_radius_m = raw_item.param2
        mission_item.yaw_deg = raw_item.param4

    elif raw_item.command == MAV_CMD.MAV_CMD_IMAGE_START_CAPTURE:
        mission_item.camera_action = CameraAction.TAKE_PHOTO

    elif raw_item.command == MAV_CMD.MAV_CMD_DO_MOUNT_CONTROL:
        mission_item.gimbal_pitch_deg = raw_item.param1
        mission_item.gimbal_yaw_deg = raw_item.param3

    return mission_item


class Drone:
    def __init__(self):
        load_dotenv()
        self.connection_string = os.getenv("CONNECTION_STRING")
        if not self.connection_string:
            raise ValueError("CONNECTION_STRING not found in .env file")
        self.system = System()

    async def connect(self):
        """Connects to the drone using the connection string from the .env file."""
        print(f"--- Connecting to drone on {self.connection_string} ---")
        await self.system.connect(system_address=self.connection_string)

        async for state in self.system.core.connection_state():
            if state.is_connected:
                print("--> Drone Connected")
                return True
        return False

    async def wait_for_readiness(self):
        """Waits for the drone to be ready (passes health checks)."""
        print("--- Waiting for drone to be ready ---")
        async for health in self.system.telemetry.health():
            if health.is_armable and health.is_global_position_ok:
                print("--> System Ready")
                break

    async def arm(self):
        """Arms the drone."""
        print("--- Arming ---")
        await self.system.action.arm()
        async for is_armed in self.system.telemetry.armed():
            if is_armed:
                print("--> Drone Armed")
                break

    async def takeoff(self, altitude=10.0):
        """Takes off to a specific altitude."""
        print(f"--- Taking off to {altitude}m ---")
        await self.system.action.set_takeoff_altitude(altitude)
        await self.system.action.takeoff()
        async for position in self.system.telemetry.position():
            if position.relative_altitude_m > altitude * 0.95:
                print(f"--> Altitude Reached: {round(position.relative_altitude_m, 1)}m")
                break

    async def upload_mission(self, mission_file_path: str):
        """Uploads a mission to the drone from a QGroundControl plan file."""
        print(f"--- Importing QGC Plan from {mission_file_path} ---")
        mission_raw_result = await self.system.mission_raw.import_qgroundcontrol_mission(mission_file_path)
        converted_mission_items = [convert_mission_raw_item_to_mission_item(item) for item in mission_raw_result.mission_items]
        mission_plan = MissionPlan(converted_mission_items)
        print(f"--- Uploading {len(converted_mission_items)} items ---")
        await self.system.mission.upload_mission(mission_plan)
        print("--> Mission Uploaded")

    async def start_mission(self):
        """Starts the uploaded mission."""
        print("--- Starting mission ---")
        await self.system.mission.set_current_mission_item(0)
        await asyncio.sleep(1)
        await self.system.mission.start_mission()

    async def monitor_mission_progress(self):
        """Monitors the mission progress and returns when complete."""
        async for progress in self.system.mission.mission_progress():
            print(f"   [Mission] Waypoint {progress.current}/{progress.total}")
            if progress.current == progress.total:
                print("-- Mission Complete")
                break

    async def is_mission_finished(self) -> bool:
        """Checks if the mission is finished."""
        return await self.system.mission.is_mission_finished()

    async def return_to_launch(self):
        """Commands the drone to return to the launch position."""
        print("--- Returning to Launch ---")
        await self.system.action.return_to_launch()

    async def hold(self):
        """Sets the drone to hold mode."""
        print("--- Setting to Hold Mode ---")
        await self.system.action.hold()
        print("--> Drone in Hold Mode")

    async def land(self):
        """Lands the drone."""
        print("--- Landing ---")
        await self.system.action.land()
        async for in_air in self.system.telemetry.in_air():
            if not in_air:
                print("--> Drone Landed")
                break

    async def disarm(self):
        """Disarms the drone."""
        print("--- Disarming ---")
        await self.system.action.disarm()

    async def shutdown(self):
        """Shuts down the connection to the drone."""
        print("--- Shutting down ---")
        # This is not a standard MAVSDK function, but represents disconnecting
        # The 'await self.system.connect()' doesn't have a clean disconnect,
        # the object just gets destroyed.
        pass
